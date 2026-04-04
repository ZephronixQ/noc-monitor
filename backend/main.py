import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Импорты
from config.inventory import OLT_LIST, SWITCH_LIST
from config.settings import POLL_INTERVAL_SEC, MAX_WORKERS
from network.olt_client import fetch_all_onu
from network.snmp_client import check_switch_snmp
from ws_manager import ws_manager

INTERNAL_STATE = {
    "olt_results": [],
    "sw_results": [], # Теперь здесь будет лежать готовая структура с папками
    "next_update_olt": 0,
    "is_updating_olt": False
}

GLOBAL_STATE = {"data": [], "next_update": 0, "is_updating": False}

def refresh_global_state():
    """Объединение данных OLT и коммутаторов"""
    # Теперь sw_results уже содержит готовый массив папок [{"name": "Олимпийский", "onus": [...]}]
    switches_node = {
        "ip": "Коммутаторы",
        "isSwitch": True,
        "ports": INTERNAL_STATE["sw_results"] 
    }
    GLOBAL_STATE["data"] = INTERNAL_STATE["olt_results"] + [switches_node]
    GLOBAL_STATE["next_update"] = INTERNAL_STATE["next_update_olt"]
    GLOBAL_STATE["is_updating"] = INTERNAL_STATE["is_updating_olt"]


async def process_single_switch(ip: str, desc: str, folder_name: str):
    """
    Обертка для опроса 1 коммутатора. 
    Она нужна, чтобы после асинхронного выполнения не потерять папку и адрес.
    """
    try:
        # Вызываем ваш текущий SNMP чек
        result = await check_switch_snmp(ip)
        
        # Если SNMP вернул модель свитча, красиво объединяем ее с адресом из HostMonitor
        # Например: "Махачкалинское шоссе 3 | ZTE 2928"
        snmp_model = result.get("contract", "")
        if snmp_model and snmp_model != "—":
            final_desc = f"{desc} | {snmp_model}"
        else:
            final_desc = desc

        return {
            "folder": folder_name,
            "data": {
                "id": ip,
                "contract": final_desc,
                "state": result.get("state", "TIMEOUT")
            }
        }
    except Exception as e:
        return {
            "folder": folder_name,
            "data": {
                "id": ip,
                "contract": desc,
                "state": "TIMEOUT"
            }
        }


async def poll_switches_loop():
    """Быстрый цикл опроса коммутаторов (раз в 10 сек)"""
    while True:
        try:
            tasks = []
            # Формируем задачи для всех коммутаторов из всех папок
            for folder_name, switches in SWITCH_LIST.items():
                for sw in switches:
                    tasks.append(process_single_switch(sw["ip"], sw["desc"], folder_name))
            
            # Выполняем их все параллельно (молниеносно)
            results = await asyncio.gather(*tasks)

            # Группируем результаты обратно по папкам для Svelte фронтенда
            folders_dict = {folder: [] for folder in SWITCH_LIST.keys()}
            for res in results:
                folders_dict[res["folder"]].append(res["data"])

            # Превращаем в массив портов: [{"name": "Олимпийский", "onus": [...]}, ...]
            formatted_folders = [{"name": name, "onus": onus} for name, onus in folders_dict.items()]

            INTERNAL_STATE["sw_results"] = formatted_folders
            refresh_global_state()
            
            await ws_manager.broadcast({
                "type": "update",
                "data": GLOBAL_STATE["data"],
                "next_update": GLOBAL_STATE["next_update"],
                "is_updating": INTERNAL_STATE["is_updating_olt"]
            })
        except Exception as e:
            print(f"Ошибка опроса коммутаторов: {e}")
        
        await asyncio.sleep(10)


async def poll_olt_loop():
    """Цикл опроса тяжелых OLT (раз в 30 мин)"""
    loop = asyncio.get_event_loop()
    while True:
        INTERNAL_STATE["is_updating_olt"] = True
        await ws_manager.broadcast({"type": "status", "is_updating": True})

        try:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                olt_tasks = [loop.run_in_executor(executor, fetch_all_onu, host) for host in OLT_LIST]
                INTERNAL_STATE["olt_results"] = list(await asyncio.gather(*olt_tasks))
        except Exception as e:
            print(f"Ошибка опроса OLT: {e}")

        INTERNAL_STATE["next_update_olt"] = int(time.time()) + POLL_INTERVAL_SEC
        INTERNAL_STATE["is_updating_olt"] = False
        
        refresh_global_state()
        await ws_manager.broadcast({
            "type": "update",
            "data": GLOBAL_STATE["data"],
            "next_update": GLOBAL_STATE["next_update"],
            "is_updating": False
        })
        await asyncio.sleep(POLL_INTERVAL_SEC)


@asynccontextmanager
async def lifespan(app: FastAPI):
    olt_task = asyncio.create_task(poll_olt_loop())
    sw_task = asyncio.create_task(poll_switches_loop())
    yield
    olt_task.cancel()
    sw_task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/data")
async def get_initial_data(): 
    refresh_global_state()
    return GLOBAL_STATE

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
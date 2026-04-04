import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config.inventory import OLT_LIST, SWITCH_LIST
from config.settings import POLL_INTERVAL_SEC, MAX_WORKERS
from network.olt_client import fetch_all_onu
from network.snmp_client import check_switch_snmp
from ws_manager import ws_manager

GLOBAL_STATE = {"data": [], "next_update": 0, "is_updating": True}

async def poll_devices_loop():
    loop = asyncio.get_event_loop()
    while True:
        GLOBAL_STATE["is_updating"] = True
        await ws_manager.broadcast({"type": "status", "is_updating": True})

        # OLT (Threads)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            olt_tasks = [loop.run_in_executor(executor, fetch_all_onu, host) for host in OLT_LIST]
            olt_results = await asyncio.gather(*olt_tasks)

        # Switches (SNMP Async)
        switch_tasks = [check_switch_snmp(ip) for ip in SWITCH_LIST]
        switch_onus = await asyncio.gather(*switch_tasks)

        switches_data = {
            "ip": "Коммутаторы",
            "isSwitch": True,
            "ports": [{"name": "Статус узлов (SNMP)", "onus": switch_onus}]
        }

        GLOBAL_STATE["data"] = list(olt_results) + [switches_data]
        GLOBAL_STATE["next_update"] = int(time.time()) + POLL_INTERVAL_SEC
        GLOBAL_STATE["is_updating"] = False
        
        await ws_manager.broadcast({
            "type": "update",
            "data": GLOBAL_STATE["data"],
            "next_update": GLOBAL_STATE["next_update"],
            "is_updating": False
        })
        await asyncio.sleep(POLL_INTERVAL_SEC)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poll_devices_loop())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/data")
async def get_initial_data(): return GLOBAL_STATE

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: ws_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
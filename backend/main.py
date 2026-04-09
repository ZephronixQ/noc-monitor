import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from config.inventory import OLT_LIST, SWITCH_LIST
from config.settings import POLL_INTERVAL_SEC, MAX_WORKERS
from network.olt_client import fetch_all_onu
from network.snmp_client import check_switch_snmp
from utils.event_logger import log_switch_event, get_history, get_daily_stats_json, save_json_db, close_all_open_incidents
from ws_manager import ws_manager

# ТЕПЕРЬ LOSI СЧИТАЕТСЯ АВАРИЕЙ СЕТИ ТАК ЖЕ, КАК LOS И DOWN
LOS_STATES = {"LOS", "DOWN", "LOSI"}

INTERNAL_STATE = {
    "olt_results": [],
    "sw_results":  [],
    "next_update_olt": 0,
    "is_updating_olt": False,
    "_prev_states": {},
    "_prev_sw_states": {},
}

GLOBAL_STATE = {"data": [], "next_update": 0, "is_updating": False}

force_update_event = asyncio.Event()

def refresh_global_state():
    switches_node = {
        "ip": "Коммутаторы",
        "isSwitch": True,
        "ports": INTERNAL_STATE["sw_results"],
    }
    GLOBAL_STATE["data"] = INTERNAL_STATE["olt_results"] + [switches_node]
    GLOBAL_STATE["next_update"] = INTERNAL_STATE["next_update_olt"]
    GLOBAL_STATE["is_updating"] = INTERNAL_STATE["is_updating_olt"]


def _track_events(olt_results: list) -> None:
    prev = INTERNAL_STATE["_prev_states"]
    curr: dict[str, dict] = {}
    now = int(time.time())

    for olt in olt_results:
        olt_ip = olt["ip"]
        for port in olt.get("ports", []):
            total_onus = len(port.get("onus", []))
            
            # В счетчик массовых аварий мы учитываем все виды обрывов
            strict_los_count = sum(1 for onu in port.get("onus", []) if onu["state"].upper() in LOS_STATES)

            for onu in port.get("onus", []):
                onu_id   = onu["id"]
                state    = onu["state"]
                contract = onu.get("contract", "—")
                key      = f"{olt_ip}:{onu_id}"

                is_los = state.upper() in LOS_STATES
                prev_data = prev.get(key, {})
                prev_state = prev_data.get("state")
                los_start = prev_data.get("los_start")

                if is_los and str(prev_state).upper() not in LOS_STATES:
                    los_start = now
                elif not is_los and str(prev_state).upper() in LOS_STATES:
                    los_start = None
                elif is_los and str(prev_state).upper() in LOS_STATES:
                    los_start = prev_data.get("los_start", now)

                curr[key] = {"state": state, "contract": contract, "onu_id": onu_id, "olt_ip": olt_ip, "los_start": los_start}
                if los_start:
                    onu["los_time"] = los_start

            if total_onus >= 8 and (strict_los_count / total_onus) > 0.60:
                port["is_mass_outage"] = True
            elif 0 < total_onus < 8 and strict_los_count == total_onus:
                port["is_mass_outage"] = True
            else:
                port["is_mass_outage"] = False

    INTERNAL_STATE["_prev_states"] = curr


async def process_single_switch(ip: str, desc: str, folder_name: str):
    try:
        result = await check_switch_snmp(ip)
        snmp_model = result.get("contract", "")
        final_desc = f"{desc} | {snmp_model}" if snmp_model and snmp_model != "—" else desc
        return {"folder": folder_name, "data": {"id": ip, "contract": final_desc, "state": result.get("state", "TIMEOUT")}}
    except Exception:
        return {"folder": folder_name, "data": {"id": ip, "contract": desc, "state": "TIMEOUT"}}


async def poll_switches_loop():
    MAX_STRIKES = 3

    while True:
        try:
            tasks = [
                process_single_switch(sw["ip"], sw["desc"], folder_name)
                for folder_name, switches in SWITCH_LIST.items()
                for sw in switches
            ]
            results = await asyncio.gather(*tasks)

            folders_dict = {folder: [] for folder in SWITCH_LIST}
            for res in results:
                folders_dict[res["folder"]].append(res["data"])

            now = int(time.time())
            prev_sw = INTERNAL_STATE.setdefault("_prev_sw_states", {})
            curr_sw = {}
            folders_list = []

            has_db_changes = False

            for name, onus in folders_dict.items():
                total_sw = len(onus)
                bad_sw = 0

                for sw in onus:
                    sw_id = sw["id"]
                    state = sw["state"]

                    is_down_snmp = state not in ["working", "Host is alive"]

                    prev_data = prev_sw.get(sw_id, {"is_down": False, "los_start": None, "strikes": 0})
                    actual_down_state = prev_data.get("is_down", False)
                    los_start = prev_data.get("los_start")
                    strikes = prev_data.get("strikes", 0)

                    if is_down_snmp:
                        if not actual_down_state:
                            strikes += 1
                            if strikes >= MAX_STRIKES:
                                actual_down_state = True
                                los_start = now
                                log_switch_event(sw_id, "start")
                                has_db_changes = True
                    else:
                        strikes = 0
                        if actual_down_state:
                            actual_down_state = False
                            los_start = None
                            log_switch_event(sw_id, "end")
                            has_db_changes = True

                    if is_down_snmp and not actual_down_state:
                        sw["state"] = "working"

                    if actual_down_state:
                        bad_sw += 1
                        sw["los_time"] = los_start

                    curr_sw[sw_id] = {"is_down": actual_down_state, "los_start": los_start, "strikes": strikes}

                is_mass = False
                if total_sw >= 5 and (bad_sw / total_sw) > 0.60:
                    is_mass = True
                elif 0 < total_sw < 5 and bad_sw == total_sw:
                    is_mass = True

                folders_list.append({"name": name, "onus": onus, "is_mass_outage": is_mass})

            INTERNAL_STATE["_prev_sw_states"] = curr_sw
            INTERNAL_STATE["sw_results"] = folders_list
            refresh_global_state()

            if has_db_changes:
                await asyncio.to_thread(save_json_db)

            await ws_manager.broadcast({
                "type": "update",
                "data": GLOBAL_STATE["data"],
                "next_update": GLOBAL_STATE["next_update"],
                "is_updating": INTERNAL_STATE["is_updating_olt"],
                "is_sw_only": True,
            })
        except Exception as e:
            print(f"❌ [SW ERROR] Ошибка цикла коммутаторов: {e}")

        await asyncio.sleep(5)


async def poll_olt_loop():
    loop = asyncio.get_event_loop()
    while True:
        INTERNAL_STATE["is_updating_olt"] = True
        await ws_manager.broadcast({"type": "status", "is_updating": True})

        try:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                olt_tasks = [loop.run_in_executor(executor, fetch_all_onu, host) for host in OLT_LIST]
                olt_results = list(await asyncio.gather(*olt_tasks))

            await asyncio.to_thread(_track_events, olt_results)
            INTERNAL_STATE["olt_results"] = olt_results

        except Exception as e:
            print(f"[OLT] Ошибка опроса: {e}")

        INTERNAL_STATE["next_update_olt"] = int(time.time()) + POLL_INTERVAL_SEC
        INTERNAL_STATE["is_updating_olt"] = False

        refresh_global_state()
        await ws_manager.broadcast({
            "type": "update",
            "data": GLOBAL_STATE["data"],
            "next_update": GLOBAL_STATE["next_update"],
            "is_updating": False,
            "is_sw_only": False,
        })
        
        try:
            await asyncio.wait_for(force_update_event.wait(), timeout=POLL_INTERVAL_SEC)
            force_update_event.clear()
        except asyncio.TimeoutError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    close_all_open_incidents()
    olt_task = asyncio.create_task(poll_olt_loop())
    sw_task  = asyncio.create_task(poll_switches_loop())
    yield
    olt_task.cancel()
    sw_task.cancel()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/data")
async def get_initial_data():
    refresh_global_state()
    return GLOBAL_STATE


@app.get("/api/stats/daily")
async def get_daily_stats():
    return get_daily_stats_json()


@app.get("/api/history/{target_id:path}")
async def get_contract_history(target_id: str, days: int = 30):
    try:
        history = get_history(target_id, days)
        return {"target_id": target_id, "days": days, "incidents": history, "total": len(history)}
    except Exception as e:
        return {"target_id": target_id, "days": days, "incidents": [], "error": str(e)}

@app.post("/api/update/force")
async def trigger_force_update():
    force_update_event.set()
    return {"status": "ok", "message": "Update triggered"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
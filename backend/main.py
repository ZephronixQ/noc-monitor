# backend/main.py
import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware

from config.inventory import OLT_DEVICES, SWITCH_LIST
from config.settings import POLL_INTERVAL_SEC
from network.olt_client import fetch_all_onu
from network.snmp_client import check_switch_snmp
from utils.event_logger import (
    log_event,
    log_switch_event, 
    log_onu_event, 
    get_history, 
    get_daily_stats_json, 
    close_all_open_incidents
)
from utils.audit_engine import build_monthly_audit
from utils.auth import (
    get_daily_password, is_ip_blocked, register_failed_attempt, 
    reset_ip_attempts, create_session_and_token, create_admin_token, verify_token_and_session, 
    log_audit_action, get_all_sessions_and_bans, kill_session, ban_ip, unban_ip, 
    clear_inactive_sessions, clear_audit_logs, ADMIN_PASSWORD_SECRET
)
from ws_manager import ws_manager

LOS_STATES = {"LOS", "DOWN", "LOSI"}

INTERNAL_STATE = {
    "olt_results": [],
    "sw_results":  [],
    "next_update_olt": 0,
    "is_updating_olt": False,
    "_prev_states": {},
    "_prev_sw_states": {},
    "_prev_olt_states": {},
}

GLOBAL_STATE = {"data": [], "next_update": 0, "is_updating": False}

force_update_event = None

def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

async def require_auth(request: Request, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    token = authorization.split(" ")[1]
    is_valid, msg = verify_token_and_session(token)
    if not is_valid:
        raise HTTPException(status_code=401, detail=msg)

async def require_admin_auth(request: Request, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуются права администратора")
    
    token = authorization.split(" ")[1]
    is_valid, msg = verify_token_and_session(token, require_admin=True)
    if not is_valid:
        raise HTTPException(status_code=403, detail=msg)

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
    prev_olts = INTERNAL_STATE.setdefault("_prev_olt_states", {})
    curr: dict[str, dict] = {}
    curr_olts: dict[str, dict] = {}
    now = int(time.time())

    for olt in olt_results:
        olt_ip = olt.get("ip")
        if not olt_ip:
            continue

        ports = olt.get("ports", [])
        total_onus_on_olt = sum(len(p.get("onus", [])) for p in ports)

        is_olt_down = (len(ports) == 0) or olt.get("is_offline", False) or (total_onus_on_olt == 0 and len(ports) > 0)
        was_olt_down = prev_olts.get(olt_ip, {}).get("is_down", False)

        if is_olt_down and not was_olt_down:
            log_event(olt_ip, "start")
        elif not is_olt_down and was_olt_down:
            log_event(olt_ip, "end")

        curr_olts[olt_ip] = {"is_down": is_olt_down}

        for port in ports:
            total_onus = len(port.get("onus", []))
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
                    log_onu_event(key, "start")
                elif not is_los and str(prev_state).upper() in LOS_STATES:
                    los_start = None
                    log_onu_event(key, "end")
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
    INTERNAL_STATE["_prev_olt_states"] = curr_olts


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
                    else:
                        strikes = 0
                        if actual_down_state:
                            actual_down_state = False
                            los_start = None
                            log_switch_event(sw_id, "end")

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
    loop = asyncio.get_running_loop()
    while True:
        INTERNAL_STATE["is_updating_olt"] = True
        await ws_manager.broadcast({"type": "status", "is_updating": True})

        try:
            olt_tasks = [loop.run_in_executor(None, fetch_all_onu, device) for device in OLT_DEVICES]
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
    global force_update_event
    force_update_event = asyncio.Event()
    
    close_all_open_incidents()
    
    olt_task = asyncio.create_task(poll_olt_loop())
    sw_task  = asyncio.create_task(poll_switches_loop())
    yield
    olt_task.cancel()
    sw_task.cancel()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- РУЧКИ АВТОРИЗАЦИИ И СЕССИЙ ---

@app.post("/api/auth/login")
async def login(request: Request, payload: dict):
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    blocked, reason, rem_seconds = is_ip_blocked(ip)
    if blocked:
        raise HTTPException(status_code=403, detail=f"Вход заблокирован ({reason})")

    password = payload.get("password", "").strip()
    if password != get_daily_password():
        res = register_failed_attempt(ip, max_attempts=3)
        if res["is_blocked"]:
            raise HTTPException(status_code=403, detail="3 ошибки! IP заблокирован на 24ч.")
        raise HTTPException(status_code=400, detail=f"Неверный пароль! Осталось попыток: {res['remaining']}")

    reset_ip_attempts(ip)
    data = create_session_and_token(ip, user_agent)
    log_audit_action(ip, f"Вход с сессией: {data['session_id'][:8]}...")
    
    return {"status": "ok", "token": data["token"], "session_id": data["session_id"]}


@app.get("/api/auth/check", dependencies=[Depends(require_auth)])
async def check_session_status():
    return {"status": "active"}


@app.post("/api/auth/admin-login")
async def admin_login(request: Request, payload: dict):
    ip = get_client_ip(request)
    password = payload.get("password", "").strip()

    if password == ADMIN_PASSWORD_SECRET:
        unban_ip(ip)
        reset_ip_attempts(ip)
        admin_token = create_admin_token(ip)
        log_audit_action(ip, "Успешный вход АДМИНА в /sessions")
        return {"status": "ok", "admin_token": admin_token}

    blocked, reason, rem_seconds = is_ip_blocked(ip)
    if blocked:
        raise HTTPException(status_code=403, detail=f"Вход заблокирован ({reason})")

    res = register_failed_attempt(ip, max_attempts=7)
    if res["is_blocked"]:
        raise HTTPException(status_code=403, detail="7 ошибок ввода админ-пароля! IP заблокирован на 24ч.")
    raise HTTPException(status_code=400, detail=f"Неверный секретный пароль! Осталось попыток: {res['remaining']}")


# --- СЕКРЕТНЫЕ РУЧКИ УПРАВЛЕНИЯ СЕССИЯМИ ---

@app.get("/api/admin/security", dependencies=[Depends(require_admin_auth)])
async def get_security_dashboard():
    return get_all_sessions_and_bans()

@app.post("/api/admin/session/kill", dependencies=[Depends(require_admin_auth)])
async def api_kill_session(request: Request, payload: dict):
    ip = get_client_ip(request)
    session_id = payload.get("session_id")
    kill_session(session_id)
    log_audit_action(ip, f"Принудительное закрытие сессии: {session_id[:8]}")
    return {"status": "ok"}

@app.post("/api/admin/ip/ban", dependencies=[Depends(require_admin_auth)])
async def api_ban_ip(request: Request, payload: dict):
    admin_ip = get_client_ip(request)
    target_ip = payload.get("ip")
    reason = payload.get("reason", "Заблокирован админом")
    
    ban_ip(target_ip, ban_type="permanent", hours=0, reason=reason)
    log_audit_action(admin_ip, f"Перманентная блокировка IP {target_ip}")
    return {"status": "ok"}

@app.post("/api/admin/ip/unban", dependencies=[Depends(require_admin_auth)])
async def api_unban_ip(request: Request, payload: dict):
    admin_ip = get_client_ip(request)
    target_ip = payload.get("ip")
    unban_ip(target_ip)
    log_audit_action(admin_ip, f"Разблокировка IP {target_ip}")
    return {"status": "ok"}

@app.post("/api/admin/sessions/clear-inactive", dependencies=[Depends(require_admin_auth)])
async def api_clear_inactive_sessions(request: Request):
    ip = get_client_ip(request)
    clear_inactive_sessions()
    log_audit_action(ip, "Очистка выбитых и неактивных сессий")
    return {"status": "ok"}

@app.post("/api/admin/logs/clear", dependencies=[Depends(require_admin_auth)])
async def api_clear_audit_logs(request: Request):
    ip = get_client_ip(request)
    clear_audit_logs()
    log_audit_action(ip, "Очистка логов аудита")
    return {"status": "ok"}

@app.get("/api/data", dependencies=[Depends(require_auth)])
async def get_initial_data():
    refresh_global_state()
    return GLOBAL_STATE

@app.get("/api/stats/daily", dependencies=[Depends(require_auth)])
async def get_daily_stats():
    return get_daily_stats_json()

@app.get("/api/history/{target_id:path}", dependencies=[Depends(require_auth)])
async def get_contract_history(target_id: str, days: int = 30):
    try:
        history = get_history(target_id, days)
        return {"target_id": target_id, "days": days, "incidents": history, "total": len(history)}
    except Exception as e:
        return {"target_id": target_id, "days": days, "incidents": [], "error": str(e)}

@app.get("/api/audit/month", dependencies=[Depends(require_auth)])
async def get_audit_month(year: int, month: int, day: int = 1, shift: str = "night"):
    try:
        return build_monthly_audit(year, month, day, shift, INTERNAL_STATE)
    except Exception as e:
        print(f"❌ [AUDIT ERROR]: {e}")
        return {"error": str(e), "calendar_days": [], "switches": [], "gpon": []}

@app.post("/api/update/force", dependencies=[Depends(require_auth)])
async def trigger_force_update(request: Request):
    ip = get_client_ip(request)
    log_audit_action(ip, "Запуск ПРИНУДИТЕЛЬНОГО сканирования сети")
    if force_update_event:
        force_update_event.set()
    return {"status": "ok", "message": "Update triggered", "operator_ip": ip}

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
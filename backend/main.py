import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "noc_project.settings")
django.setup()

import asyncio
import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.wsgi import WSGIMiddleware
from django.core.wsgi import get_wsgi_application
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

from inventory.models import Incident
from inventory.auth_service import generate_operator_token, verify_token
from inventory.audit_engine import build_monthly_audit
from poller.engine import (
    INTERNAL_STATE, GLOBAL_STATE, force_update_event,
    restore_active_incidents_from_db, poll_switches_loop, poll_olt_loop, refresh_global_state
)
from ws_manager import ws_manager


async def require_auth(request: Request, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    token = authorization.split(" ")[1]
    is_valid, payload = verify_token(token)
    if not is_valid:
        raise HTTPException(status_code=401, detail=payload)
    return payload


@asynccontextmanager
async def lifespan(app: FastAPI):
    @sync_to_async
    def ensure_superuser():
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@noc.local", "admin2026")
            print("👤 [AUTH] Создан дефолтный суперпользователь: admin / admin2026")
    await ensure_superuser()

    restore_active_incidents_from_db()
    refresh_global_state()

    sw_task = asyncio.create_task(poll_switches_loop(ws_manager.broadcast))
    olt_task = asyncio.create_task(poll_olt_loop(ws_manager.broadcast))
    
    yield
    sw_task.cancel()
    olt_task.cancel()


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.mount("/admin", WSGIMiddleware(get_wsgi_application()))

@app.post("/api/auth/login")
async def login(payload: dict):
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()

    if not username or not password:
        raise HTTPException(status_code=400, detail="Укажите логин и пароль")

    user = await sync_to_async(authenticate)(username=username, password=password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    token = generate_operator_token(user)
    return {
        "status": "ok",
        "token": token,
        "user": {"username": user.username, "is_staff": user.is_staff}
    }


@app.get("/api/data", dependencies=[Depends(require_auth)])
async def get_initial_data():
    refresh_global_state()
    return GLOBAL_STATE


@app.get("/api/stats/daily", dependencies=[Depends(require_auth)])
async def get_daily_stats():
    now = int(time.time())
    cutoff = now - 86400
    
    @sync_to_async
    def query_stats():
        total_24h = Incident.objects.filter(start_time__gte=cutoff).count()
        active_now = Incident.objects.filter(end_time__isnull=True).count()
        closed_24h = Incident.objects.filter(end_time__gte=cutoff, start_time__gte=cutoff)
        avg_seconds = sum(i.duration for i in closed_24h) / max(1, closed_24h.count())
        return total_24h, active_now, int(avg_seconds // 60)

    t_24h, act, avg_min = await query_stats()
    return {"total_24h": t_24h, "avg_repair_minutes": avg_min, "active_now": act}


@app.get("/api/history/{target_id:path}", dependencies=[Depends(require_auth)])
async def get_contract_history(target_id: str, days: int = 30):
    now = int(time.time())
    cutoff = now - (days * 86400)
    clean = target_id.strip().lower()

    @sync_to_async
    def query_history():
        if ":" in clean:
            parts = clean.split(":")
            q = Incident.objects.filter(target_id__icontains=parts[-1])
        else:
            q = Incident.objects.filter(target_id__iexact=clean)
            
        rows = list(q.filter(start_time__gte=cutoff).order_by('-start_time'))
        out = []
        for inc in rows:
            out.append({
                "start_time": inc.start_time,
                "end_time": inc.end_time,
                "duration": inc.duration or (now - inc.start_time),
                "start_human": datetime.fromtimestamp(inc.start_time).strftime('%d.%m.%Y %H:%M:%S'),
                "end_human": datetime.fromtimestamp(inc.end_time).strftime('%d.%m.%Y %H:%M:%S') if inc.end_time else "Актуально (Всё ещё DOWN)"
            })
        return out

    history = await query_history()
    return {"target_id": target_id, "days": days, "incidents": history, "total": len(history)}


@app.get("/api/audit/month", dependencies=[Depends(require_auth)])
async def get_audit_month(year: int, month: int, day: int = 1, shift: str = "night"):
    return await sync_to_async(build_monthly_audit)(year, month, day, shift, INTERNAL_STATE)


@app.post("/api/update/force", dependencies=[Depends(require_auth)])
async def trigger_force_update():
    force_update_event.set()
    return {"status": "ok", "message": "Принудительный опрос запущен"}


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
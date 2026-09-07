import time
from datetime import datetime
from fastapi import APIRouter, Depends
from asgiref.sync import sync_to_async
from django.db import close_old_connections
from django.db.models import Q

from inventory.models import Incident
from inventory.views_auth import require_auth
from inventory.audit_engine import build_monthly_audit
from poller.engine import GLOBAL_STATE, INTERNAL_STATE, force_update_event, refresh_global_state

api_router = APIRouter(prefix="/api", tags=["Monitoring API"], dependencies=[Depends(require_auth)])


@api_router.get("/data")
async def get_initial_data():
    refresh_global_state()
    return GLOBAL_STATE


@api_router.get("/stats/daily")
async def get_daily_stats():
    now = int(time.time())
    cutoff = now - 86400
    
    @sync_to_async
    def query_stats():
        close_old_connections()
        try:
            total_24h = Incident.objects.filter(start_time__gte=cutoff).count()
            active_now = Incident.objects.filter(end_time__isnull=True).count()
            closed_24h = Incident.objects.filter(end_time__gte=cutoff, start_time__gte=cutoff)
            avg_seconds = sum(i.duration for i in closed_24h) / max(1, closed_24h.count())
            return total_24h, active_now, int(avg_seconds // 60)
        finally:
            close_old_connections()

    t_24h, act, avg_min = await query_stats()
    return {"total_24h": t_24h, "avg_repair_minutes": avg_min, "active_now": act}


@api_router.get("/history/{target_id:path}")
async def get_contract_history(target_id: str, days: int = 365):
    now = int(time.time())
    cutoff = now - (days * 86400)
    clean = target_id.strip()

    @sync_to_async
    def query_history():
        close_old_connections()
        try:
            q = Incident.objects.filter(target_id__iexact=clean)

            if not q.exists() and ":" in clean:
                parts = clean.split(":")
                olt_ip = parts[0]
                pure_onu = parts[-1]
                
                q = Incident.objects.filter(
                    Q(target_id__iexact=clean) |
                    Q(target_id=f"{olt_ip}:{pure_onu}") |
                    (Q(target_id__istartswith=olt_ip) & Q(target_id__iendswith=f":{pure_onu}"))
                )

            rows = list(q.filter(Q(start_time__gte=cutoff) | Q(end_time__isnull=True)).order_by('-start_time'))
            
            out = []
            for inc in rows:
                dur = inc.duration if inc.end_time else max(0, now - inc.start_time)
                out.append({
                    "start_time": inc.start_time,
                    "end_time": inc.end_time,
                    "duration": dur,
                    "contract": inc.contract or "—",
                    "start_human": datetime.fromtimestamp(inc.start_time).strftime('%d.%m.%Y %H:%M:%S'),
                    "end_human": datetime.fromtimestamp(inc.end_time).strftime('%d.%m.%Y %H:%M:%S') if inc.end_time else "Актуально (Всё ещё DOWN)"
                })
            return out
        finally:
            close_old_connections()

    history = await query_history()
    print(f"📖 [DB HISTORY] Запрос узла '{clean}'. Найдено записей: {len(history)}")
    return {"target_id": target_id, "days": days, "incidents": history, "total": len(history)}


@api_router.get("/audit/month")
async def get_audit_month(year: int, month: int, day: int = 1, shift: str = "night"):
    return await sync_to_async(build_monthly_audit)(year, month, day, shift, INTERNAL_STATE)


@api_router.post("/update/force")
async def trigger_force_update():
    force_update_event.set()
    return {"status": "ok", "message": "Принудительный опрос запущен"}
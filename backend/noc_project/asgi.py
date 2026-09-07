import os
import django
from pathlib import Path
from contextlib import asynccontextmanager

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "noc_project.settings")
django.setup()

import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.wsgi import WSGIMiddleware
from django.core.wsgi import get_wsgi_application
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

from noc_project.ws import ws_manager
from inventory.views_auth import auth_router
from inventory.api import api_router
from poller.engine import (
    poll_switches_loop, 
    poll_olt_loop, 
    refresh_global_state
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    @sync_to_async
    def sync_admin_user():
        admin_user = os.getenv("DJANGO_ADMIN_USER", "admin")
        admin_pass = os.getenv("DJANGO_ADMIN_PASSWORD", "admin2026")

        user, created = User.objects.get_or_create(
            username=admin_user, 
            defaults={"email": "admin@noc.local", "is_staff": True, "is_superuser": True}
        )
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(admin_pass)
        user.save()
        if created:
            print(f"✨ [AUTH] Создан новый суперпользователь: '{admin_user}'")
        else:
            print(f"🔄 [AUTH] Пароль пользователя '{admin_user}' успешно обновлен из .env")

    await sync_admin_user()

    refresh_global_state()

    sw_task = asyncio.create_task(poll_switches_loop(ws_manager.broadcast))
    olt_task = asyncio.create_task(poll_olt_loop(ws_manager.broadcast))
    
    yield
    
    sw_task.cancel()
    olt_task.cancel()


app = FastAPI(title="NOC Monitor Enterprise", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router)
app.include_router(api_router)

admin_static_dir = Path(django.__file__).parent / "contrib" / "admin" / "static" / "admin"
if admin_static_dir.exists():
    app.mount("/static/admin", StaticFiles(directory=admin_static_dir), name="admin_static")

app.mount("/admin", WSGIMiddleware(get_wsgi_application()))

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
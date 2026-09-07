import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "noc_project.settings")
django.setup()

import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.wsgi import WSGIMiddleware
from django.core.wsgi import get_wsgi_application

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
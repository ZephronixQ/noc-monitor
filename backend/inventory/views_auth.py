from fastapi import APIRouter, HTTPException, Header, Depends
from django.contrib.auth import authenticate
from asgiref.sync import sync_to_async
from inventory.auth_service import generate_operator_token, verify_token

auth_router = APIRouter(prefix="/api/auth", tags=["Auth"])

async def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется заголовок Authorization: Bearer <token>")
    
    token = authorization.split(" ")[1]
    is_valid, payload = verify_token(token)
    if not is_valid:
        print(f"🔒 [AUTH REJECTED 401] {payload}")
        raise HTTPException(status_code=401, detail=str(payload))
    return payload

@auth_router.post("/login")
async def login(payload: dict):
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()

    if not username or not password:
        raise HTTPException(status_code=400, detail="Заполните имя пользователя и пароль")

    user = await sync_to_async(authenticate)(username=username, password=password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = generate_operator_token(user)
    return {
        "status": "ok",
        "token": token,
        "user": {"username": user.username, "is_staff": user.is_staff}
    }

@auth_router.get("/check", dependencies=[Depends(require_auth)])
async def check_session():
    return {"status": "active"}
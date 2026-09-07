import time
import json
import base64
import hmac
import hashlib
from django.conf import settings

ONE_YEAR_SECONDS = 365 * 24 * 60 * 60

def b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')

def b64_decode(data: str) -> bytes:
    rem = len(data) % 4
    if rem > 0:
        data += '=' * (4 - rem)
    return base64.urlsafe_b64decode(data)

def generate_operator_token(user) -> str:
    now = int(time.time())
    exp = now + ONE_YEAR_SECONDS
    
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.username,
        "uid": user.id,
        "is_staff": user.is_staff,
        "iat": now,
        "exp": exp
    }
    
    h_b64 = b64_encode(json.dumps(header).encode())
    p_b64 = b64_encode(json.dumps(payload).encode())
    sig_input = f"{h_b64}.{p_b64}".encode()
    signature = b64_encode(hmac.new(settings.SECRET_KEY.encode(), sig_input, hashlib.sha256).digest())
    
    return f"{h_b64}.{p_b64}.{signature}"

def verify_token(token: str) -> tuple[bool, dict | str]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return False, "Неверный формат токена"
            
        h_b64, p_b64, sig_b64 = parts
        sig_input = f"{h_b64}.{p_b64}".encode()
        expected_sig = b64_encode(hmac.new(settings.SECRET_KEY.encode(), sig_input, hashlib.sha256).digest())
        
        if not hmac.compare_digest(sig_b64, expected_sig):
            return False, "Недействительная подпись токена (ключ SECRET_KEY изменился)"
            
        payload = json.loads(b64_decode(p_b64).decode())
        if payload.get("exp", 0) < int(time.time()):
            return False, "Срок действия сессии истек"
            
        return True, payload
    except Exception as e:
        return False, f"Ошибка проверки токена: {e}"
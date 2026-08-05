# backend/utils/auth.py
import time
import sqlite3
import hmac
import hashlib
import json
import base64
import uuid
from datetime import datetime
from config.inventory import ADMIN_PASSWORD_SECRET
from utils.event_logger import DB_PATH, db_lock

SECRET_KEY = "NOC_MONITOR_ENTERPRISE_SECRET_KEY_2026"

def init_security_db():
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_sessions (
                session_id TEXT PRIMARY KEY,
                ip TEXT NOT NULL,
                user_agent TEXT,
                created_at INTEGER NOT NULL,
                last_seen INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_blacklist (
                ip TEXT PRIMARY KEY,
                ban_type TEXT NOT NULL,
                blocked_until INTEGER DEFAULT 0,
                reason TEXT,
                created_at INTEGER NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_bans (
                ip TEXT PRIMARY KEY,
                attempts INTEGER DEFAULT 0,
                blocked_until INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp INTEGER NOT NULL
            )
        """)
        conn.commit()
        conn.close()

init_security_db()

def b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')

def b64_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def get_daily_password() -> str:
    return datetime.now().strftime("%d%m%Y")

def is_ip_blocked(ip: str) -> tuple[bool, str, int]:
    now = int(time.time())
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT ban_type, blocked_until, reason FROM ip_blacklist WHERE ip = ?", (ip,))
        black = cursor.fetchone()
        if black:
            ban_type, blocked_until, reason = black
            if ban_type == 'permanent':
                conn.close()
                return True, "НАВСЕГДА (Заблокирован админом)", 0
            elif ban_type == 'temp' and blocked_until > now:
                conn.close()
                return True, f"ВРЕМЕННО ({reason})", blocked_until - now

        cursor.execute("SELECT blocked_until FROM ip_bans WHERE ip = ?", (ip,))
        row = cursor.fetchone()
        conn.close()

        if row and row[0] > now:
            return True, "Заблокирован за 3 неверных ввода", row[0] - now

        return False, "", 0

def register_failed_attempt(ip: str, max_attempts: int = 3) -> dict:
    now = int(time.time())
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT attempts FROM ip_bans WHERE ip = ?", (ip,))
        row = cursor.fetchone()

        if not row:
            cursor.execute("INSERT INTO ip_bans (ip, attempts, blocked_until) VALUES (?, 1, 0)", (ip,))
            attempts = 1
        else:
            attempts = row[0] + 1
            if attempts >= max_attempts:
                blocked_until = now + (24 * 3600)
                cursor.execute("UPDATE ip_bans SET attempts = ?, blocked_until = ? WHERE ip = ?", (attempts, blocked_until, ip))
                conn.commit()
                conn.close()
                return {"is_blocked": True, "attempts": attempts, "blocked_for_hours": 24}

            cursor.execute("UPDATE ip_bans SET attempts = ? WHERE ip = ?", (attempts, ip))

        conn.commit()
        conn.close()
        return {"is_blocked": False, "attempts": attempts, "remaining": max_attempts - attempts}

def reset_ip_attempts(ip: str):
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ip_bans WHERE ip = ?", (ip,))
        conn.commit()
        conn.close()

def create_session_and_token(ip: str, user_agent: str) -> dict:
    session_id = str(uuid.uuid4())
    now = int(time.time())
    midnight = int(datetime.combine(datetime.now().date(), datetime.max.time()).timestamp())
    
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO active_sessions (session_id, ip, user_agent, created_at, last_seen, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (session_id, ip, user_agent, now, now))
        conn.commit()
        conn.close()

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "session_id": session_id,
        "ip": ip,
        "exp": midnight,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "role": "user"
    }
    
    header_b64 = b64_encode(json.dumps(header).encode())
    payload_b64 = b64_encode(json.dumps(payload).encode())
    signature_input = f"{header_b64}.{payload_b64}".encode()
    sig_b64 = b64_encode(hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest())
    
    token = f"{header_b64}.{payload_b64}.{sig_b64}"
    return {"token": token, "session_id": session_id}

def create_admin_token(ip: str) -> str:
    now = datetime.now()
    midnight = int(datetime.combine(now.date(), datetime.max.time()).timestamp())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "ip": ip,
        "exp": midnight,
        "date": now.strftime("%Y-%m-%d"),
        "role": "admin"
    }
    header_b64 = b64_encode(json.dumps(header).encode())
    payload_b64 = b64_encode(json.dumps(payload).encode())
    signature_input = f"{header_b64}.{payload_b64}".encode()
    sig_b64 = b64_encode(hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest())
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_token_and_session(token: str, require_admin: bool = False) -> tuple[bool, str]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return False, "Неверный формат"
        
        header_b64, payload_b64, sig_b64 = parts
        signature_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = b64_encode(hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest())
        
        if not hmac.compare_digest(sig_b64, expected_sig):
            return False, "Неверная подпись"
            
        payload = json.loads(b64_decode(payload_b64).decode())
        session_id = payload.get("session_id")
        ip = payload.get("ip")
        role = payload.get("role", "user")
        
        # АДМИНУ ВСЕГДА РАЗРЕШЕН ДОСТУП ДЛЯ УПРАВЛЕНИЯ БАНАМИ И СЕССИЯМИ
        if require_admin:
            if role != "admin":
                return False, "Требуются права Администратора"
            return True, "OK"

        if payload.get("exp", 0) < int(time.time()) or payload.get("date") != datetime.now().strftime("%Y-%m-%d"):
            return False, "Сессия истекла (наступили 00:00)"

        blocked, reason, _ = is_ip_blocked(ip)
        if blocked:
            return False, f"Вход заблокирован ({reason})"

        if session_id:
            with db_lock:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT is_active FROM active_sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                
                if row and row[0] == 1:
                    cursor.execute("UPDATE active_sessions SET last_seen = ? WHERE session_id = ?", (int(time.time()), session_id))
                    conn.commit()
                    conn.close()
                    return True, "OK"
                
                conn.close()
                return False, "Сессия аннулирована администратором"

        return True, "OK"

    except Exception as e:
        return False, str(e)

def get_all_sessions_and_bans() -> dict:
    now = int(time.time())
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Сессии
        cursor.execute("""
            SELECT session_id, ip, user_agent, created_at, last_seen, is_active 
            FROM active_sessions 
            ORDER BY last_seen DESC
        """)
        sessions = [
            {
                "session_id": r[0], "ip": r[1], "user_agent": r[2], 
                "created_at": r[3], "last_seen": r[4], "is_active": bool(r[5]),
                "is_online": (now - r[4]) < 30 and bool(r[5])
            }
            for r in cursor.fetchall()
        ]
        
        # 2. ВСЕ БАНЫ (Ручные + Авто-баны)
        bans_map = {}
        cursor.execute("SELECT ip, ban_type, blocked_until, reason, created_at FROM ip_blacklist")
        for r in cursor.fetchall():
            bans_map[r[0]] = {"ip": r[0], "ban_type": r[1], "blocked_until": r[2], "reason": r[3] or "Заблокирован админом", "created_at": r[4]}

        cursor.execute("SELECT ip, blocked_until FROM ip_bans WHERE blocked_until > ?", (now,))
        for r in cursor.fetchall():
            ip, blocked_until = r[0], r[1]
            if ip not in bans_map:
                bans_map[ip] = {"ip": ip, "ban_type": "temp", "blocked_until": blocked_until, "reason": "3 неверных ввода пароля", "created_at": now}

        bans = list(bans_map.values())

        # 3. Аудит логи
        cursor.execute("""
            SELECT ip, action, timestamp 
            FROM audit_logs 
            ORDER BY timestamp DESC LIMIT 50
        """)
        logs = [
            {"ip": r[0], "action": r[1], "timestamp": r[2]}
            for r in cursor.fetchall()
        ]
        
        conn.close()
    return {"sessions": sessions, "bans": bans, "logs": logs}

def clear_inactive_sessions():
    """Очищает неактивные / выбитые сессии, оставляя ТОЛЬКО ЖИВЫЕ"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM active_sessions WHERE is_active = 0")
        conn.commit()
        conn.close()

def clear_audit_logs():
    """Очищает историю аудита"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM audit_logs")
        conn.commit()
        conn.close()

def kill_session(session_id: str):
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE active_sessions SET is_active = 0 WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

def ban_ip(ip: str, ban_type: str = "permanent", hours: int = 0, reason: str = "Ручной бан"):
    now = int(time.time())
    blocked_until = (now + hours * 3600) if ban_type == 'temp' else 0
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO ip_blacklist (ip, ban_type, blocked_until, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (ip, ban_type, blocked_until, reason, now))
        cursor.execute("UPDATE active_sessions SET is_active = 0 WHERE ip = ?", (ip,))
        conn.commit()
        conn.close()

def unban_ip(ip: str):
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ip_blacklist WHERE ip = ?", (ip,))
        cursor.execute("DELETE FROM ip_bans WHERE ip = ?", (ip,))
        conn.commit()
        conn.close()

def log_audit_action(ip: str, action: str):
    now = int(time.time())
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO audit_logs (ip, action, timestamp) VALUES (?, ?, ?)", (ip, action, now))
        conn.commit()
        conn.close()
    print(f"🚨 [AUDIT LOG] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | IP: {ip} | Действие: {action}")
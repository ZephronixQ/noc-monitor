# backend\utils\event_logger.py
import os
import sqlite3
import time
import threading
from datetime import datetime

# Путь к новой базе данных SQLite
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "noc_history.db")

# Глобальная блокировка записи для предотвращения "database is locked" при параллельных запросах
db_lock = threading.Lock()

def init_db():
    """Инициализация таблиц базы данных и создание быстрых индексов"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Таблица инцидентов падения связи
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id TEXT NOT NULL,
                start_time INTEGER NOT NULL,
                end_time INTEGER,
                duration INTEGER DEFAULT 0
            )
        """)
        
        # Создаем индексы для мгновенной выборки на больших объемах данных
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_target ON incidents (target_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_start ON incidents (start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_end ON incidents (end_time)")
        
        conn.commit()
        conn.close()

# Запуск инициализации бд при старте бэкенда
init_db()

def close_all_open_incidents():
    """При перезапуске сервера закрываем все висящие (незакрытые) аварии текущим временем"""
    now = int(time.time())
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Находим незакрытые сессии
        cursor.execute("SELECT target_id, start_time FROM incidents WHERE end_time IS NULL")
        open_cases = cursor.fetchall()
        
        if open_cases:
            cursor.execute("""
                UPDATE incidents
                SET end_time = ?, duration = ? - start_time
                WHERE end_time IS NULL
            """, (now, now))
            conn.commit()
            
            for target, start_t in open_cases:
                start_human = datetime.fromtimestamp(start_t).strftime('%d.%m.%Y %H:%M')
                print(f"🔧 [SQLITE] Закрыта висячая авария: {target} (старт: {start_human})")
                
        conn.close()

def log_event(target_id: str, action: str):
    """
    Универсальная потокобезопасная функция логирования событий для коммутаторов и ONU.
    target_id: IP коммутатора или составной ONU_ID ("IP_OLT:Интерфейс:Индекс")
    """
    now = int(time.time())
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if action == "start":
            # Проверяем, нет ли уже открытой аварии для этого узла
            cursor.execute("SELECT id FROM incidents WHERE target_id = ? AND end_time IS NULL", (target_id,))
            exists = cursor.fetchone()
            if not exists:
                cursor.execute("""
                    INSERT INTO incidents (target_id, start_time, end_time, duration)
                    VALUES (?, ?, NULL, 0)
                """, (target_id, now))
                conn.commit()
        
        elif action == "end":
            # Закрываем аварийную сессию
            cursor.execute("""
                UPDATE incidents
                SET end_time = ?, duration = ? - start_time
                WHERE target_id = ? AND end_time IS NULL
            """, (now, now, target_id))
            conn.commit()
            
        conn.close()

def log_switch_event(ip: str, action: str):
    """Логирование коммутатора (алиас для обратной совместимости)"""
    log_event(ip, action)

def log_onu_event(onu_id: str, action: str):
    """Логирование GPON ONU"""
    log_event(onu_id, action)

def get_history(target_id: str, days: int = 30) -> list:
    """Извлечение истории инцидентов для конкретного хоста за последние N дней"""
    now = int(time.time())
    cutoff = now - (days * 86400)
    results = []
    
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Достаем инциденты, попадающие в выбранный диапазон дней
        cursor.execute("""
            SELECT start_time, end_time, duration
            FROM incidents
            WHERE target_id = ? AND (start_time >= ? OR end_time IS NULL)
            ORDER BY start_time DESC
        """, (target_id, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
    for start_time, end_time, duration in rows:
        d = {
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "start_human": datetime.fromtimestamp(start_time).strftime('%d.%m.%Y %H:%M:%S')
        }
        
        if end_time:
            d["end_human"] = datetime.fromtimestamp(end_time).strftime('%d.%m.%Y %H:%M:%S')
        else:
            d["end_human"] = "Актуально (Всё ещё DOWN)"
            d["duration"] = now - start_time
            
        results.append(d)
        
    return results

def get_daily_stats_json():
    """Сбор статистики по авариям за последние 24 часа"""
    now = int(time.time())
    cutoff = now - 86400
    
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Всего аварий за 24 часа (активные + закрытые в эти сутки)
        cursor.execute("""
            SELECT COUNT(*) FROM incidents 
            WHERE start_time >= ? OR (end_time IS NULL OR end_time >= ?)
        """, (cutoff, cutoff))
        total_24h = cursor.fetchone()[0]
        
        # 2. Активные аварии прямо сейчас
        cursor.execute("SELECT COUNT(*) FROM incidents WHERE end_time IS NULL")
        active_now = cursor.fetchone()[0]
        
        # 3. Среднее время устранения (только закрытые инциденты за 24 часа)
        cursor.execute("""
            SELECT AVG(duration) FROM incidents 
            WHERE end_time >= ? AND start_time >= ? AND end_time IS NOT NULL
        """, (cutoff, cutoff))
        avg_res = cursor.fetchone()[0]
        
        conn.close()
        
    avg_minutes = int(avg_res // 60) if avg_res else 0
    
    return {
        "total_24h": total_24h, 
        "avg_repair_minutes": avg_minutes, 
        "active_now": active_now
    }

# Пустая функция-заглушка для совместимости, так как SQLite фиксирует изменения на лету и сохранение вручную больше не требуется
def save_json_db():
    pass
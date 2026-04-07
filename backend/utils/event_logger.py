import os
import json
import time
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DB_DIR, exist_ok=True)
JSON_PATH = os.path.join(DB_DIR, "switches_history.json")

HISTORY_DATA = {}

def load_json_db():
    global HISTORY_DATA
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                HISTORY_DATA = json.load(f)
        except Exception:
            HISTORY_DATA = {}
    else:
        HISTORY_DATA = {}

def save_json_db():
    try:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(HISTORY_DATA, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка записи JSON: {e}")

load_json_db()

def close_all_open_incidents():
    """При рестарте сервера закрываем все незакрытые инциденты.
    Они висят потому что _prev_sw_states сбросился и 'end' уже никогда не придёт."""
    global HISTORY_DATA
    now = int(time.time())
    changed = False

    for ip, events in HISTORY_DATA.items():
        for ev in events:
            if ev.get("end_time") is None:
                ev["end_time"] = now
                ev["duration"] = now - ev["start_time"]
                changed = True
                print(f"🔧 Закрыт висячий инцидент: {ip} (старт: {datetime.fromtimestamp(ev['start_time']).strftime('%d.%m.%Y %H:%M')})")

    if changed:
        save_json_db()

def log_switch_event(ip: str, action: str):
    global HISTORY_DATA
    now = int(time.time())
    
    if ip not in HISTORY_DATA:
        HISTORY_DATA[ip] = []
        
    events = HISTORY_DATA[ip]
    
    if action == "start":
        if not events or events[-1].get("end_time") is not None:
            events.append({"start_time": now, "end_time": None, "duration": 0})
    elif action == "end":
        if events and events[-1].get("end_time") is None:
            events[-1]["end_time"] = now
            events[-1]["duration"] = now - events[-1]["start_time"]

def get_history(target_id: str, days: int = 30) -> list:
    global HISTORY_DATA
    now = int(time.time())
    cutoff = now - (days * 86400)
    
    events = HISTORY_DATA.get(target_id, [])
    results = []
    
    for ev in reversed(events):
        start_time = ev["start_time"]
        end_time = ev["end_time"]
        
        if start_time < cutoff and end_time is not None and end_time < cutoff:
            continue
            
        d = {
            "start_time": start_time,
            "end_time": end_time,
            "duration": ev["duration"],
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
    global HISTORY_DATA
    now = int(time.time())
    cutoff = now - 86400
    
    total_24h = 0
    active_now = 0
    total_duration = 0
    closed_events = 0
    
    for ip, events in HISTORY_DATA.items():
        for ev in events:
            if ev["start_time"] >= cutoff or (ev["end_time"] is None or ev["end_time"] >= cutoff):
                total_24h += 1
                if ev["end_time"] is None:
                    active_now += 1
                else:
                    closed_events += 1
                    total_duration += ev["duration"]
                    
    avg_minutes = int((total_duration / closed_events) // 60) if closed_events > 0 else 0
    
    return {"total_24h": total_24h, "avg_repair_minutes": avg_minutes, "active_now": active_now}
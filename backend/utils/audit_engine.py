# backend/utils/audit_engine.py
import time
import sqlite3
import calendar
from datetime import datetime, timedelta
from config.inventory import SWITCH_LIST
from utils.event_logger import DB_PATH, db_lock

def format_sec_to_str(seconds: int) -> str:
    if not seconds or seconds <= 0:
        return "0 мин"
    m = seconds // 60
    h = m // 60
    d = h // 24
    if d > 0:
        return f"{d} дн {h % 24} ч"
    if h > 0:
        return f"{h} ч {m % 60} мин"
    return f"{m} мин"

def build_inventory_maps():
    sw_map = {}
    for folder_name, switches in SWITCH_LIST.items():
        for sw in switches:
            ip = sw["ip"].strip().lower()
            sw_map[ip] = {
                "location": folder_name,
                "contract": sw.get("desc", "—")
            }
    return sw_map

def build_gpon_live_maps(internal_state: dict):
    """Сбор карт портов, договоров и живых статусов ONU (СТРОГО ДЛЯ СВЯЗИ LOS)"""
    now = int(time.time())
    live_incidents = []
    onu_contract_map = {}
    onu_port_map = {}
    live_state_map = {}

    if not internal_state:
        return live_incidents, onu_contract_map, onu_port_map, live_state_map

    # 1. Коммутаторы
    for folder in internal_state.get("sw_results", []):
        for sw in folder.get("onus", []):
            state = str(sw.get("state", "")).strip().lower()
            sw_id = str(sw.get("id", "")).strip().lower()
            is_down = state not in ["working", "host is alive"]
            live_state_map[sw_id] = "DOWN" if is_down else "WORKING"

            if is_down:
                los_time = sw.get("los_time") or now
                live_incidents.append({
                    "target_id": sw.get("id"),
                    "start_time": los_time,
                    "end_time": None,
                    "duration": now - los_time
                })

    # 2. ONU GPON (СТРОГО ТОЛЬКО СВЯЗЬ LOS И DOWN)
    for olt in internal_state.get("olt_results", []):
        olt_ip = olt.get("ip", "")
        for port in olt.get("ports", []):
            port_name = port.get("name", "1/1")
            for onu in port.get("onus", []):
                state = str(onu.get("state", "")).strip().upper()
                raw_id = str(onu.get("id", "")).strip()
                pure_id = raw_id.split(":")[-1] # Извлекаем чистый номер ONU
                contract = onu.get("contract", "—")
                
                full_key = f"{olt_ip}:{port_name}:{pure_id}".lower()
                short_key = f"{olt_ip}:{pure_id}".lower()
                raw_key = f"{olt_ip}:{raw_id}".lower()
                
                for k in [full_key, short_key, raw_key]:
                    live_state_map[k] = state
                    onu_port_map[k] = port_name
                    if contract and contract != "—":
                        onu_contract_map[k] = contract

                # СТРОГО СВЯЗЬ LOS / DOWN
                if state in ["LOS", "DOWN"]:
                    los_time = onu.get("los_time") or now
                    live_incidents.append({
                        "target_id": full_key,
                        "start_time": los_time,
                        "end_time": None,
                        "duration": now - los_time
                    })

    return live_incidents, onu_contract_map, onu_port_map, live_state_map

def get_shift_timestamps(year: int, month: int, day: int, shift: str):
    dt_day = datetime(year, month, day)
    if shift == "night":
        start_dt = dt_day.replace(hour=17, minute=0, second=0)
        end_dt = (dt_day + timedelta(days=1)).replace(hour=9, minute=0, second=0)
    else:
        start_dt = dt_day.replace(hour=0, minute=0, second=0)
        end_dt = dt_day.replace(hour=23, minute=59, second=59)
        
    return int(start_dt.timestamp()), int(end_dt.timestamp())

def filter_strict_los_incidents(incidents_list, year, month, day, shift, now, live_state_map):
    """Фильтрация аварий дня (ТОЛЬКО СТРОГИЕ ОБРЫВЫ LOS)"""
    s_ts, e_ts = get_shift_timestamps(year, month, day, shift)
    valid_incidents = []

    for inc in incidents_list:
        actual_end = inc["end_time"] or now
        if (inc["start_time"] <= e_ts) and (actual_end >= s_ts):
            target = inc["target_id"].lower().strip()
            
            # Для GPON проверяем статус: строго LOS или DOWN
            if ":" in target:
                st = live_state_map.get(target, "LOS")
                if st not in ["LOS", "DOWN"]:
                    continue # Пропускаем LOSi / Working / Offline
            
            valid_incidents.append(inc)

    return valid_incidents

def build_monthly_audit(year: int, month: int, selected_day: int, shift: str = "night", internal_state: dict = None):
    now = int(time.time())
    sw_map = build_inventory_maps()
    live_incidents, onu_contract_map, onu_port_map, live_state_map = build_gpon_live_maps(internal_state or {})
    
    _, num_days = calendar.monthrange(year, month)
    first_day_ts = int(datetime(year, month, 1, 0, 0, 0).timestamp()) - 86400
    last_day_ts = int(datetime(year, month, num_days, 23, 59, 59).timestamp()) + 86400
    
    # 1. Извлечение истории из SQLite
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT target_id, start_time, end_time, duration
            FROM incidents
            WHERE start_time <= ? AND (end_time >= ? OR end_time IS NULL)
            ORDER BY start_time ASC
        """, (last_day_ts, first_day_ts))
        rows = cursor.fetchall()
        conn.close()

    all_incidents = []
    existing_targets = set()
    
    for target_id, s_time, e_time, dur in rows:
        target_clean = target_id.lower().strip()
        
        # Пропускаем, если текущий статус устройства LOSi
        if e_time is None and ":" in target_clean and live_state_map.get(target_clean) == "LOSI":
            continue
            
        all_incidents.append({
            "target_id": target_id,
            "start_time": s_time,
            "end_time": e_time,
            "duration": e_time - s_time if e_time else now - s_time
        })
        if e_time is None:
            existing_targets.add(target_id)

    # 2. Добавление живых активных LOS аварий
    for live_inc in live_incidents:
        if live_inc["target_id"] not in existing_targets:
            all_incidents.append(live_inc)

    # 3. Подсчет аварий для табло календаря (ИСПРАВЛЕНО: КЛЮЧИ hasProblem И has_problem)
    calendar_days = []
    for d in range(1, num_days + 1):
        day_incs = filter_strict_los_incidents(all_incidents, year, month, d, shift, now, live_state_map)
        day_count = len(day_incs)
        
        calendar_days.append({
            "day": d,
            "hasProblem": day_count > 0,
            "has_problem": day_count > 0,
            "count": day_count
        })

    # 4. Сборка аварий для выбранного дня
    sel_incidents = filter_strict_los_incidents(all_incidents, year, month, selected_day, shift, now, live_state_map)

    sw_groups_raw = {}
    gpon_olts_raw = {}

    for inc in sel_incidents:
        target = inc["target_id"]
        
        # Коммутаторы
        if ":" not in target:
            ip = target.strip().lower()
            info = sw_map.get(ip, {"location": "Коммутаторы на ONU", "contract": "—"})
            loc = info["location"]
            
            if loc not in sw_groups_raw:
                sw_groups_raw[loc] = {}
            if ip not in sw_groups_raw[loc]:
                sw_groups_raw[loc][ip] = {"ip": target, "contract": info["contract"], "events": []}
            
            sw_groups_raw[loc][ip]["events"].append(inc)

        # GPON (СТРОГО ТОЛЬКО СВЯЗЬ LOS)
        else:
            parts = target.split(":")
            if len(parts) >= 2:
                olt_ip = parts[0]
                onu_id = parts[-1]
                
                # Поиск настоящей платы
                short_key = f"{olt_ip}:{onu_id}".lower()
                full_key = f"{olt_ip}:{parts[1] if len(parts)==3 else ''}:{onu_id}".lower()
                
                port_name = (parts[1] if len(parts) == 3 else None) or onu_port_map.get(short_key) or onu_port_map.get(full_key) or "1/1"
                
                if olt_ip not in gpon_olts_raw:
                    gpon_olts_raw[olt_ip] = {}
                if port_name not in gpon_olts_raw[olt_ip]:
                    gpon_olts_raw[olt_ip][port_name] = {}
                
                gpon_olts_raw[olt_ip][port_name][onu_id] = inc

    # Сериализация Свичей
    formatted_switches = []
    for loc_name, sw_dict in sw_groups_raw.items():
        folder_items = []
        for ip, sw_data in sw_dict.items():
            ev_list = sw_data["events"]
            ev_list.sort(key=lambda x: x["start_time"])
            
            if len(ev_list) == 1:
                e = ev_list[0]
                folder_items.append({
                    "is_cluster": False,
                    "id": e["target_id"],
                    "contract": sw_data["contract"],
                    "time_start": datetime.fromtimestamp(e["start_time"]).strftime("%H:%M"),
                    "time_end": datetime.fromtimestamp(e["end_time"]).strftime("%H:%M") if e["end_time"] else "Активен",
                    "duration_sec": e["duration"],
                    "duration_str": format_sec_to_str(e["duration"])
                })
            else:
                first = ev_list[0]
                last = ev_list[-1]
                total_dur = sum(e["duration"] for e in ev_list)
                
                history_list = []
                for e in ev_list:
                    history_list.append({
                        "start": datetime.fromtimestamp(e["start_time"]).strftime("%H:%M"),
                        "end": datetime.fromtimestamp(e["end_time"]).strftime("%H:%M") if e["end_time"] else "Активен",
                        "duration_str": format_sec_to_str(e["duration"])
                    })
                    
                folder_items.append({
                    "is_cluster": True,
                    "id": first["target_id"],
                    "contract": sw_data["contract"],
                    "time_start": datetime.fromtimestamp(first["start_time"]).strftime("%H:%M"),
                    "time_end": datetime.fromtimestamp(last["end_time"]).strftime("%H:%M") if last["end_time"] else "Активен",
                    "duration_sec": total_dur,
                    "duration_str": format_sec_to_str(total_dur),
                    "history": history_list
                })
                
        formatted_switches.append({
            "folder_name": loc_name,
            "items": folder_items
        })

    # Сериализация GPON
    formatted_gpon = []
    for olt_ip, ports_dict in gpon_olts_raw.items():
        ports_list = []
        olt_los = 0
        
        for port_name, onus_dict in ports_dict.items():
            onus_list = []
            port_los = 0
            
            for onu_id, e in onus_dict.items():
                full_key = f"{olt_ip}:{port_name}:{onu_id}".lower()
                short_key = f"{olt_ip}:{onu_id}".lower()
                contract = onu_contract_map.get(full_key) or onu_contract_map.get(short_key) or "—"
                
                port_los += 1
                olt_los += 1
                
                onus_list.append({
                    "id": onu_id,
                    "contract": contract,
                    "state": "LOS",
                    "time_start": datetime.fromtimestamp(e["start_time"]).strftime("%H:%M"),
                    "time_end": datetime.fromtimestamp(e["end_time"]).strftime("%H:%M") if e["end_time"] else "Активен",
                    "duration_str": format_sec_to_str(e["duration"])
                })
                
            ports_list.append({
                "port_name": port_name, 
                "los_count": port_los,
                "onus": onus_list
            })
            
        formatted_gpon.append({
            "olt_ip": olt_ip, 
            "los_count": olt_los,
            "ports": ports_list
        })

    return {
        "year": year,
        "month": month,
        "selected_day": selected_day,
        "shift": shift,
        "calendar_days": calendar_days,
        "switches": formatted_switches,
        "gpon": formatted_gpon
    }
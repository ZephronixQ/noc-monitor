import calendar
from datetime import datetime, timedelta
from django.utils import timezone
from inventory.models import Incident, Switch, Cluster

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

def get_shift_timestamps(year: int, month: int, day: int, shift: str):
    dt_day = datetime(year, month, day)
    if shift == "night":
        start_dt = dt_day.replace(hour=17, minute=0, second=0)
        end_dt = (dt_day + timedelta(days=1)).replace(hour=9, minute=0, second=0)
    else:
        start_dt = dt_day.replace(hour=0, minute=0, second=0)
        end_dt = dt_day.replace(hour=23, minute=59, second=59)
    return int(start_dt.timestamp()), int(end_dt.timestamp())

def build_monthly_audit(year: int, month: int, selected_day: int, shift: str = "night", internal_state: dict = None):
    now = int(timezone.now().timestamp())
    _, num_days = calendar.monthrange(year, month)
    
    first_day_ts = int(datetime(year, month, 1, 0, 0, 0).timestamp()) - 86400
    last_day_ts = int(datetime(year, month, num_days, 23, 59, 59).timestamp()) + 86400

    db_incidents = list(Incident.objects.filter(
        start_time__lte=last_day_ts
    ).filter(
        end_time__gte=first_day_ts
    ) | Incident.objects.filter(
        start_time__lte=last_day_ts,
        end_time__isnull=True
    ))

    sw_map = {sw.ip: {"desc": sw.description, "location": sw.cluster.name} for sw in Switch.objects.select_related('cluster').all()}

    onu_contract_map = {}
    onu_live_state = {}

    if internal_state and "olt_results" in internal_state:
        for olt in internal_state.get("olt_results", []):
            olt_ip = olt.get("ip", "")
            for port in olt.get("ports", []):
                port_name = port.get("name", "")
                for onu in port.get("onus", []):
                    raw_id = str(onu.get("id", ""))
                    pure_id = raw_id.split(":")[-1]
                    contract = onu.get("contract", "")
                    state = str(onu.get("state", "")).strip().upper()

                    full_key = f"{olt_ip}:{port_name}:{pure_id}".lower()
                    short_key = f"{olt_ip}:{pure_id}".lower()

                    onu_live_state[full_key] = state
                    onu_live_state[short_key] = state

                    if contract and contract not in ["—", "-", ""]:
                        onu_contract_map[full_key] = contract
                        onu_contract_map[short_key] = contract

    calendar_days = []
    for d in range(1, num_days + 1):
        s_ts, e_ts = get_shift_timestamps(year, month, d, shift)
        day_count = sum(1 for inc in db_incidents if inc.start_time <= e_ts and (inc.end_time or now) >= s_ts)
        calendar_days.append({
            "day": d,
            "hasProblem": day_count > 0,
            "count": day_count
        })

    sel_s_ts, sel_e_ts = get_shift_timestamps(year, month, selected_day, shift)
    sel_incidents = [inc for inc in db_incidents if inc.start_time <= sel_e_ts and (inc.end_time or now) >= sel_s_ts]

    sw_groups_raw = {}
    gpon_olts_raw = {}

    for inc in sel_incidents:
        target = inc.target_id
        
        if inc.device_type == 'sw' or (':' not in target and inc.device_type != 'olt'):
            info = sw_map.get(target, {"location": "Коммутаторы на ONU", "desc": inc.contract or "—"})
            loc = info["location"]
            final_contract = info["desc"] if info["desc"] != "—" else (inc.contract or "—")
            sw_groups_raw.setdefault(loc, {}).setdefault(target, {"contract": final_contract, "events": []})
            sw_groups_raw[loc][target]["events"].append(inc)

        elif inc.device_type == 'onu' or ':' in target:
            parts = target.split(":")
            olt_ip = parts[0]
            onu_id = parts[-1]
            port_name = parts[1] if len(parts) == 3 else "1/1"
            
            gpon_olts_raw.setdefault(olt_ip, {}).setdefault(port_name, {}).setdefault(onu_id, []).append(inc)

    formatted_switches = []
    for loc_name, sw_dict in sw_groups_raw.items():
        folder_items = []
        for ip, data in sw_dict.items():
            ev_list = sorted(data["events"], key=lambda x: x.start_time)
            first, last = ev_list[0], ev_list[-1]
            total_dur = sum((e.end_time or now) - e.start_time for e in ev_list)

            if len(ev_list) == 1:
                folder_items.append({
                    "is_cluster": False,
                    "id": ip,
                    "contract": data["contract"],
                    "time_start": datetime.fromtimestamp(first.start_time).strftime("%H:%M"),
                    "time_end": datetime.fromtimestamp(first.end_time).strftime("%H:%M") if first.end_time else "Активен",
                    "duration_sec": total_dur,
                    "duration_str": format_sec_to_str(total_dur)
                })
            else:
                history = [{
                    "start": datetime.fromtimestamp(e.start_time).strftime("%H:%M"),
                    "end": datetime.fromtimestamp(e.end_time).strftime("%H:%M") if e.end_time else "Активен",
                    "duration_str": format_sec_to_str((e.end_time or now) - e.start_time)
                } for e in ev_list]

                folder_items.append({
                    "is_cluster": True,
                    "id": ip,
                    "contract": data["contract"],
                    "time_start": datetime.fromtimestamp(first.start_time).strftime("%H:%M"),
                    "time_end": datetime.fromtimestamp(last.end_time).strftime("%H:%M") if last.end_time else "Активен",
                    "duration_sec": total_dur,
                    "duration_str": format_sec_to_str(total_dur),
                    "history": history
                })
        formatted_switches.append({"folder_name": loc_name, "items": folder_items})

    formatted_gpon = []
    for olt_ip, ports_dict in gpon_olts_raw.items():
        ports_list = []
        olt_los = 0
        
        for port_name, onus_dict in ports_dict.items():
            onus_list = []
            
            for onu_id, ev_list in onus_dict.items():
                ev_list = sorted(ev_list, key=lambda x: x.start_time)
                first, last = ev_list[0], ev_list[-1]
                total_dur = sum((e.end_time or now) - e.start_time for e in ev_list)

                lookup_full = f"{olt_ip}:{port_name}:{onu_id}".lower()
                lookup_short = f"{olt_ip}:{onu_id}".lower()

                found_contract = getattr(first, 'contract', '—')
                if not found_contract or found_contract in ["—", "-"]:
                    found_contract = onu_contract_map.get(lookup_full) or onu_contract_map.get(lookup_short) or "—"

                is_currently_down = (last.end_time is None) and (onu_live_state.get(lookup_full, "LOS") in ["LOS", "DOWN"])
                time_end_str = "Активен" if is_currently_down else datetime.fromtimestamp(last.end_time or now).strftime("%H:%M")

                olt_los += 1

                if len(ev_list) == 1:
                    onus_list.append({
                        "is_cluster": False,
                        "id": onu_id,
                        "contract": found_contract,
                        "state": "LOS",
                        "time_start": datetime.fromtimestamp(first.start_time).strftime("%H:%M"),
                        "time_end": time_end_str,
                        "duration_str": format_sec_to_str(total_dur)
                    })
                else:
                    history = [{
                        "start": datetime.fromtimestamp(e.start_time).strftime("%H:%M"),
                        "end": datetime.fromtimestamp(e.end_time).strftime("%H:%M") if e.end_time else "Активен",
                        "duration_str": format_sec_to_str((e.end_time or now) - e.start_time)
                    } for e in ev_list]

                    onus_list.append({
                        "is_cluster": True,
                        "id": onu_id,
                        "contract": found_contract,
                        "state": "LOS",
                        "time_start": datetime.fromtimestamp(first.start_time).strftime("%H:%M"),
                        "time_end": time_end_str,
                        "duration_str": format_sec_to_str(total_dur),
                        "history": history
                    })

            ports_list.append({"port_name": port_name, "los_count": len(onus_list), "onus": onus_list})
        formatted_gpon.append({"olt_ip": olt_ip, "los_count": olt_los, "ports": ports_list})

    return {
        "year": year,
        "month": month,
        "selected_day": selected_day,
        "shift": shift,
        "calendar_days": calendar_days,
        "switches": formatted_switches,
        "gpon": formatted_gpon
    }
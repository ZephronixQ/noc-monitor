# backend\network\olt_client.py
import re
from netmiko import ConnectHandler
from collections import defaultdict
from utils.parser import parse_onu_line, RE_DESCRIPTION

# Регулярка для извлечения Cause C300
RE_CAUSE = re.compile(r'20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+(LOSi|LOS)', re.IGNORECASE)

# Регулярка для извлечения договора (User-Defined-Rid) на C600
RE_C600_RID = re.compile(r'User-Defined-Rid\s*:\s*(\S+)', re.IGNORECASE)


def get_onu_details_c300(conn, pon_port, onu_id, current_state):
    """Опрашивает детальную информацию для C300/C320, достает описание и причину LOS"""
    for iface in [f"gpon-onu_{pon_port}:{onu_id}", f"{pon_port}:{onu_id}"]:
        try:
            out = conn.send_command(f"show gpon onu detail-info {iface}", read_timeout=15)
            
            # Парсинг Description
            m = RE_DESCRIPTION.search(out)
            desc = m.group(1) if m else "—"
            
            # Парсинг Cause
            cause = current_state
            if current_state.lower() in ["los", "down"]:
                causes = RE_CAUSE.findall(out)
                if causes:
                    cause = causes[-1].upper() 

            return desc, cause
        except:
            continue
    return "—", current_state


def get_onu_details_c600(conn, pon_port, onu_id):
    """Опрашивает виртуальный порт vport на C600 и извлекает договор клиента"""
    try:
        cmd = f"show port-identification port vport-{pon_port}.1:{onu_id} service-port 1"
        out = conn.send_command(cmd, read_timeout=15)
        
        m = RE_C600_RID.search(out)
        desc = m.group(1) if m else "—"
        return desc
    except Exception as e:
        print(f"❌ [C600] Ошибка парсинга vport {pon_port}:{onu_id}: {e}")
        return "—"


def fetch_all_onu(device_config: dict):
    # ИСПРАВЛЕНО: Извлекаем параметры по ключу "asdzx1390" в соответствии с вашей конфигурацией
    host = device_config["host"]
    username = device_config["username"]
    password = device_config["asdzx1390"]
    port = device_config.get("port", 23)
    model_type = device_config.get("type", "c300").lower()

    device = {
        "device_type": "zte_zxros_telnet",
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "conn_timeout": 15,
    }
    try:
        conn = ConnectHandler(**device)
        conn.send_command("terminal length 0", read_timeout=10)
        output = conn.send_command("show gpon onu state", read_timeout=120)

        ports = defaultdict(list)
        for line in output.splitlines():
            parsed = parse_onu_line(line)
            if parsed:
                p, i, s = parsed
                ports[p].append((i, s))

        frontend_ports = []
        for pon_port, onus in ports.items():
            port_onus = []
            for onu_id, state in onus:
                safe_state = str(state).lower()
                
                if model_type == "c600":
                    desc = get_onu_details_c600(conn, pon_port, onu_id)
                    actual_state = state
                else:
                    if safe_state in ["los", "down"]:
                        desc, actual_state = get_onu_details_c300(conn, pon_port, onu_id, safe_state)
                    else:
                        desc = "—" 
                        actual_state = state
                
                port_onus.append({"id": f"{pon_port}:{onu_id}", "contract": desc, "state": actual_state})
            
            frontend_ports.append({"name": pon_port, "onus": port_onus})

        conn.disconnect()
        return {"ip": host, "isSwitch": False, "ports": frontend_ports}
    except Exception as e:
        return {"ip": host, "isSwitch": False, "ports": [], "error": str(e)}
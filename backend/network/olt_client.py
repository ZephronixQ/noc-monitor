import re
from netmiko import ConnectHandler
from collections import defaultdict
from config.inventory import DEFAULT_USER, DEFAULT_PASS
from utils.parser import parse_onu_line, RE_DESCRIPTION

# Регулярка для извлечения Cause (опираемся только на строки с валидным годом 20xx)
RE_CAUSE = re.compile(r'20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+(LOSi|LOS)', re.IGNORECASE)

def get_onu_details(conn, pon_port, onu_id, current_state):
    """ Опрашивает детальную информацию, достает описание и настоящую причину (LOS / LOSi) """
    for iface in [f"gpon-onu_{pon_port}:{onu_id}", f"{pon_port}:{onu_id}"]:
        try:
            out = conn.send_command(f"show gpon onu detail-info {iface}", read_timeout=15)
            
            # Парсинг Description
            m = RE_DESCRIPTION.search(out)
            desc = m.group(1) if m else "—"
            
            # Парсинг Cause
            cause = current_state
            if current_state.lower() in ["los", "down"]:
                # Ищем все реальные отключения (игнорируем нули 0000-00-00)
                causes = RE_CAUSE.findall(out)
                if causes:
                    # [-1] берет самый последний (свежий) записанный инцидент из таблицы
                    cause = causes[-1].upper() 

            return desc, cause
        except:
            continue
    return "—", current_state


def fetch_all_onu(host):
    device = {
        "device_type": "zte_zxros_telnet",
        "host": host,
        "username": DEFAULT_USER,
        "password": DEFAULT_PASS,
        "conn_timeout": 10,
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
                
                if safe_state in ["los", "down"]:
                    desc, actual_state = get_onu_details(conn, pon_port, onu_id, safe_state)
                else:
                    desc = "—" 
                    actual_state = state
                
                port_onus.append({"id": f"{pon_port}:{onu_id}", "contract": desc, "state": actual_state})
            
            frontend_ports.append({"name": pon_port, "onus": port_onus})

        conn.disconnect()
        return {"ip": host, "isSwitch": False, "ports": frontend_ports}
    except Exception as e:
        return {"ip": host, "isSwitch": False, "ports": [], "error": str(e)}
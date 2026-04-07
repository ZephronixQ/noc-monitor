from netmiko import ConnectHandler
from collections import defaultdict
from config.inventory import DEFAULT_USER, DEFAULT_PASS
from utils.parser import parse_onu_line, RE_DESCRIPTION

def get_description(conn, pon_port, onu_id):
    for iface in [f"gpon-onu_{pon_port}:{onu_id}", f"{pon_port}:{onu_id}"]:
        try:
            out = conn.send_command(f"show gpon onu detail-info {iface}", read_timeout=15)
            m = RE_DESCRIPTION.search(out)
            if m: return m.group(1)
        except: continue
    return "—"

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
                
                # Приводим статус к нижнему регистру для надежной проверки
                safe_state = str(state).lower()
                
                # Опрашиваем договор ТОЛЬКО если статус 'los' или 'down'
                if safe_state in ["los", "down"]:
                    desc = get_description(conn, pon_port, onu_id)
                else:
                    desc = "—" # Для working, offline, dyinggasp и прочих запросы НЕ делаем!
                
                port_onus.append({"id": f"{pon_port}:{onu_id}", "contract": desc, "state": state})
            
            frontend_ports.append({"name": pon_port, "onus": port_onus})

        conn.disconnect()
        return {"ip": host, "isSwitch": False, "ports": frontend_ports}
    except Exception as e:
        return {"ip": host, "isSwitch": False, "ports": [], "error": str(e)}
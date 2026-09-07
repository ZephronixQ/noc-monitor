import re
from netmiko import ConnectHandler
from collections import defaultdict

RE_FMT_A = re.compile(r'^gpon-onu_(\d+/\d+/\d+):(\d+)\s+\S+\s+\S+\s+\S+\s+(\S+)')
RE_FMT_B = re.compile(r'^(\d+/\d+/\d+):(\d+)\s+\S+\s+\S+\s+(\S+)\s+\S+')
RE_DESCRIPTION = re.compile(r'Description:\s*(\S+)')
RE_CAUSE = re.compile(r'20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+(LOSi|LOS)', re.IGNORECASE)
RE_C600_RID = re.compile(r'User-Defined-Rid\s*:\s*(\S+)', re.IGNORECASE)

ONU_STATES = {"LOS", "DyingGasp", "OffLine", "working", "losi", "down"}


def parse_onu_line(line: str):
    line = line.strip()
    for regex in [RE_FMT_A, RE_FMT_B]:
        m = regex.match(line)
        if m:
            pon_port, onu_id, state = m.group(1), m.group(2), m.group(3)
            if state in ONU_STATES or state.lower() in ["los", "working", "losi", "dyinggasp"]:
                return pon_port, onu_id, state
    return None


def get_onu_details_c300(conn, pon_port, onu_id, current_state):
    for iface in [f"gpon-onu_{pon_port}:{onu_id}", f"{pon_port}:{onu_id}"]:
        try:
            out = conn.send_command(f"show gpon onu detail-info {iface}", read_timeout=15)
            m = RE_DESCRIPTION.search(out)
            desc = m.group(1) if m else "—"
            
            cause = current_state
            if current_state.lower() in ["los", "down"]:
                causes = RE_CAUSE.findall(out)
                if causes:
                    cause = causes[-1].upper()
            return desc, cause
        except Exception:
            continue
    return "—", current_state


def get_onu_details_c600(conn, pon_port, onu_id):
    try:
        cmd = f"show port-identification port vport-{pon_port}.1:{onu_id} service-port 1"
        out = conn.send_command(cmd, read_timeout=15)
        m = RE_C600_RID.search(out)
        return m.group(1) if m else "—"
    except Exception:
        return "—"


def poll_single_olt(olt_model) -> dict:
    """Опрос одной OLT станции из модели Django OltDevice"""
    host = olt_model.ip
    username = olt_model.username
    password = olt_model.password
    port = olt_model.port
    model_type = olt_model.model_type.lower()

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
                
                port_onus.append({
                    "id": f"{pon_port}:{onu_id}",
                    "contract": desc,
                    "state": actual_state
                })
            
            frontend_ports.append({"name": pon_port, "onus": port_onus})

        conn.disconnect()
        return {"ip": host, "isSwitch": False, "ports": frontend_ports, "is_offline": False}

    except Exception as e:
        return {"ip": host, "isSwitch": False, "ports": [], "is_offline": True, "error": str(e)}
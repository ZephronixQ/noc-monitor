import os
import sys
import asyncio
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity, get_cmd
)

GLOBAL_SNMP_ENGINE = SnmpEngine()
OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"

ENV_SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY", "public")
ENV_SNMP_PORT = int(os.getenv("SNMP_PORT", "161"))


async def async_icmp_ping(ip: str) -> bool:
    try:
        cmd = ["ping", "-n", "1", "-w", "1000", ip] if sys.platform == "win32" else ["ping", "-c", "1", "-W", "1", ip]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        return (await proc.wait()) == 0
    except Exception:
        return False


def clean_model_name(raw_descr: str) -> str:
    if not raw_descr or raw_descr.strip() in ["", "—"]:
        return "L2 Switch"
    clean = " ".join(raw_descr.split())
    for word in ["Ethernet Switch", "Device, Compiled", "ROM: System", "Software, Version"]:
        if word in clean:
            clean = clean.split(word)[0].strip()
    return clean[:40].strip()


async def check_switch_status(ip: str, community: str = None, port: int = None) -> dict:
    target_community = community or ENV_SNMP_COMMUNITY
    target_port = port or ENV_SNMP_PORT

    try:
        transport = await UdpTransportTarget.create((ip, target_port), timeout=2.0, retries=1)
        error_indication, error_status, _, var_binds = await get_cmd(
            GLOBAL_SNMP_ENGINE,
            CommunityData(target_community, mpModel=1),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(OID_SYS_DESCR))
        )

        if not error_indication and not error_status and var_binds:
            raw_descr = str(var_binds[0][1])
            model_str = clean_model_name(raw_descr)
            return {"id": ip, "snmp_ok": True, "ping_ok": True, "model": model_str}
    except Exception:
        pass

    ping_ok = await async_icmp_ping(ip)
    return {
        "id": ip,
        "snmp_ok": False,
        "ping_ok": ping_ok,
        "model": "L2 Switch"
    }

check_switch_snmp = check_switch_status
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity, get_cmd
)
from config.inventory import SNMP_COMMUNITY_RO, SNMP_PORT
from config.settings import OID_SYS_DESCR
from utils.parser import parse_sys_descr

# Создаем ОДИН глобальный движок на всё приложение!
# Это спасет сервер от зависания (Event Loop Death)
GLOBAL_SNMP_ENGINE = SnmpEngine()

async def check_switch_snmp(ip: str):
    try:
        # Используем глобальный движок вместо создания нового
        transport = await UdpTransportTarget.create((ip, SNMP_PORT), timeout=2.0, retries=1)
        error_indication, error_status, _, var_binds = await get_cmd(
            GLOBAL_SNMP_ENGINE,
            CommunityData(SNMP_COMMUNITY_RO, mpModel=1),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(OID_SYS_DESCR))
        )

        if error_indication or error_status:
            return {"id": ip, "contract": "Timeout / Unreachable", "state": "LOS"}

        raw_descr = str(var_binds[0][1])
        parsed = parse_sys_descr(raw_descr)
        model_str = f"{parsed['vendor']} {parsed['model']}" if parsed else raw_descr[:30]
        return {"id": ip, "contract": model_str, "state": "working"}

    except Exception:
        return {"id": ip, "contract": "SNMP Error", "state": "LOS"}
    # Блок finally с close_dispatcher() удален, так как движок теперь вечный
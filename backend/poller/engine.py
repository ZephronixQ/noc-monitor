import asyncio
import time
from datetime import datetime
from asgiref.sync import sync_to_async
from django.db import close_old_connections

from inventory.models import Switch, Cluster, OltDevice, Incident
from poller.snmp import check_switch_status
from poller.olt_worker import poll_single_olt

POLL_INTERVAL_SEC = 1800  # 30 минут круг OLT
LOS_STATES = {"LOS", "DOWN", "LOSI"}

INTERNAL_STATE = {
    "olt_results": [],
    "sw_results": [],
    "next_update_olt": 0,
    "is_updating_olt": False,
}

GLOBAL_STATE = {"data": [], "next_update": 0, "is_updating": False}
force_update_event = asyncio.Event()


def db_record_start(target_id: str, device_type: str, now_ts: int):
    close_old_connections()
    try:
        clean_target = target_id.strip()
        inc = Incident.objects.filter(target_id__iexact=clean_target, end_time__isnull=True).first()
        if not inc:
            inc = Incident.objects.create(
                target_id=clean_target,
                device_type=device_type,
                start_time=now_ts,
                duration=0
            )
            print(f"🚨 [DB RECORD CREATED] Авария записана в БД: {clean_target} ({device_type})")
        return inc.start_time
    except Exception as e:
        print(f"❌ [DB CREATE ERROR] {target_id}: {e}")
        return now_ts
    finally:
        close_old_connections()


def db_record_end(target_id: str, now_ts: int):
    close_old_connections()
    try:
        clean_target = target_id.strip()
        open_incs = list(Incident.objects.filter(target_id__iexact=clean_target, end_time__isnull=True))
        for inc in open_incs:
            inc.close(end_ts=now_ts)
            print(f"✅ [DB RECORD CLOSED] Авария закрыта в БД: {clean_target} (простой: {inc.duration} сек)")
    except Exception as e:
        print(f"❌ [DB CLOSE ERROR] {target_id}: {e}")
    finally:
        close_old_connections()


@sync_to_async
def sync_switch_to_db(sw_id: str, is_down: bool, now_ts: int):
    if is_down:
        start_ts = db_record_start(sw_id, 'sw', now_ts)
        return True, start_ts
    else:
        db_record_end(sw_id, now_ts)
        return False, None


STRICT_LOS_STATES = {"LOS", "DOWN"}


@sync_to_async
def sync_gpon_to_db(olt_results: list, now_ts: int):
    close_old_connections()
    try:
        for olt in olt_results:
            olt_ip = olt.get("ip")
            if not olt_ip:
                continue

            ports = olt.get("ports", [])
            is_olt_down = len(ports) == 0 or olt.get("is_offline", False)

            if is_olt_down:
                db_record_start(olt_ip, 'olt', now_ts)
            else:
                db_record_end(olt_ip, now_ts)

            for port in ports:
                for onu in port.get("onus", []):
                    onu_id = onu.get("id", "")
                    state = str(onu.get("state", "")).strip().upper()
                    key = f"{olt_ip}:{onu_id}"

                    if state in STRICT_LOS_STATES:
                        start_ts = db_record_start(key, 'onu', now_ts)
                        onu["los_time"] = start_ts
                    else:
                        db_record_end(key, now_ts)
                        if state == "WORKING":
                            onu["los_time"] = None
    finally:
        close_old_connections()


@sync_to_async
def get_active_inventory():
    close_old_connections()
    try:
        clusters = list(Cluster.objects.prefetch_related('switches').all())
        olts = list(OltDevice.objects.filter(is_active=True))
        
        switch_inventory = {}
        for cl in clusters:
            active_sws = [sw for sw in cl.switches.all() if sw.is_active]
            if active_sws:
                switch_inventory[cl.name] = [
                    {"ip": sw.ip, "desc": sw.description, "override": sw.model_override}
                    for sw in active_sws
                ]
        return switch_inventory, olts
    finally:
        close_old_connections()


def refresh_global_state():
    switches_node = {
        "ip": "Коммутаторы",
        "isSwitch": True,
        "ports": INTERNAL_STATE["sw_results"],
    }
    GLOBAL_STATE["data"] = INTERNAL_STATE["olt_results"] + [switches_node]
    GLOBAL_STATE["next_update"] = INTERNAL_STATE["next_update_olt"]
    GLOBAL_STATE["is_updating"] = INTERNAL_STATE["is_updating_olt"]


async def process_single_switch(ip: str, desc: str, folder_name: str, override: str):
    res = await check_switch_status(ip)
    snmp_ok = res.get("snmp_ok", False)
    ping_ok = res.get("ping_ok", False)
    fetched_model = res.get("model", "")

    model = override if override else (fetched_model if snmp_ok else "L2 Switch")
    final_desc = f"{desc} | {model}" if desc and desc != "—" else desc

    is_alive = snmp_ok or ping_ok
    proto = "SNMP" if snmp_ok else ("PING" if ping_ok else "NONE")

    return {
        "folder": folder_name,
        "data": {
            "id": ip,
            "contract": final_desc,
            "is_alive": is_alive,
            "proto": proto
        }
    }


async def poll_switches_loop(broadcast_callback):
    while True:
        try:
            switch_inventory, _ = await get_active_inventory()
            now = int(time.time())

            tasks = [
                process_single_switch(sw["ip"], sw["desc"], folder_name, sw.get("override", ""))
                for folder_name, switches in switch_inventory.items()
                for sw in switches
            ]

            results = await asyncio.gather(*tasks) if tasks else []

            folders_dict = {f: [] for f in switch_inventory}
            for r in results:
                folders_dict[r["folder"]].append(r["data"])

            folders_list = []

            for name, items in folders_dict.items():
                total_sw = len(items)
                bad_sw = 0
                processed_onus = []

                for item in items:
                    sw_id = item["id"]
                    is_alive = item["is_alive"]

                    is_down = not is_alive

                    is_down_in_db, los_start_ts = await sync_switch_to_db(sw_id, is_down, now)

                    if is_down_in_db:
                        bad_sw += 1
                        state_str = "LOS"
                        los_time = los_start_ts
                    else:
                        state_str = "working"
                        los_time = None

                    processed_onus.append({
                        "id": sw_id,
                        "contract": item["contract"],
                        "state": state_str,
                        "proto": item["proto"],
                        "los_time": los_time
                    })

                is_mass = (total_sw >= 5 and (bad_sw / total_sw) > 0.60) or (0 < total_sw < 5 and bad_sw == total_sw)
                folders_list.append({"name": name, "onus": processed_onus, "is_mass_outage": is_mass})

            INTERNAL_STATE["sw_results"] = folders_list
            refresh_global_state()

            await broadcast_callback({
                "type": "update",
                "data": GLOBAL_STATE["data"],
                "next_update": GLOBAL_STATE["next_update"],
                "is_updating": INTERNAL_STATE["is_updating_olt"],
                "is_sw_only": True,
            })

        except Exception as e:
            print(f"❌ [SW POLLER ERROR]: {e}")

        await asyncio.sleep(5)


async def poll_olt_loop(broadcast_callback):
    loop = asyncio.get_running_loop()
    
    while True:
        INTERNAL_STATE["is_updating_olt"] = True
        await broadcast_callback({"type": "status", "is_updating": True})

        try:
            _, olts = await get_active_inventory()
            now = int(time.time())

            olt_tasks = [loop.run_in_executor(None, poll_single_olt, olt_dev) for olt_dev in olts]
            olt_results = list(await asyncio.gather(*olt_tasks)) if olt_tasks else []

            await sync_gpon_to_db(olt_results, now)

            INTERNAL_STATE["olt_results"] = olt_results

        except Exception as e:
            print(f"❌ [OLT POLLER ERROR]: {e}")

        INTERNAL_STATE["next_update_olt"] = int(time.time()) + POLL_INTERVAL_SEC
        INTERNAL_STATE["is_updating_olt"] = False
        refresh_global_state()

        await broadcast_callback({
            "type": "update",
            "data": GLOBAL_STATE["data"],
            "next_update": GLOBAL_STATE["next_update"],
            "is_updating": False,
            "is_sw_only": False,
        })

        try:
            await asyncio.wait_for(force_update_event.wait(), timeout=POLL_INTERVAL_SEC)
            force_update_event.clear()
        except asyncio.TimeoutError:
            pass
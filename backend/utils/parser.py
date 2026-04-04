import re
from config.settings import ONU_STATES, VENDOR_PATTERNS, SNR_MODEL_MAP

RE_FMT_A = re.compile(r'^gpon-onu_(\d+/\d+/\d+):(\d+)\s+\S+\s+\S+\s+\S+\s+(\S+)')
RE_FMT_B = re.compile(r'^(\d+/\d+/\d+):(\d+)\s+\S+\s+\S+\s+(\S+)\s+\S+')
RE_DESCRIPTION = re.compile(r'Description:\s*(\S+)')

def parse_onu_line(line: str):
    line = line.strip()
    for regex in [RE_FMT_A, RE_FMT_B]:
        m = regex.match(line)
        if m:
            pon_port, onu_id, state = m.group(1), m.group(2), m.group(3)
            if state in ONU_STATES:
                return pon_port, onu_id, state
    return None

def parse_sys_descr(sys_descr: str) -> dict | None:
    sys_descr = " ".join(sys_descr.split())
    for vendor, pattern in VENDOR_PATTERNS.items():
        match = re.search(pattern, sys_descr)
        if not match: continue

        if vendor == "ZTE":
            return {"vendor": "ZTE", "model": match.group(1).replace(" ", "-")}
        if vendor == "SNR":
            raw_model = match.group(1)
            mapped = SNR_MODEL_MAP.get(raw_model)
            return {"vendor": "SNR", "model": mapped["model"] if mapped else raw_model}
        if vendor == "DLINK":
            return {"vendor": "D-Link", "model": match.group(1)}
        if vendor == "ELTEX":
            return {"vendor": "ELTEX", "model": match.group(1)}
    return None
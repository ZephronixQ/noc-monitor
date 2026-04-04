# Настройки опроса
MAX_WORKERS = 10
POLL_INTERVAL_SEC = 1800  # 30 минут

# Состояния ONU
ONU_STATES = {"LOS", "DyingGasp", "OffLine", "working"}

# SNMP OID и паттерны вендоров
OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"

VENDOR_PATTERNS = {
    "ZTE": r"ZTE\s+Ethernet\s+Switch\s+(ZXR10\s+\S+?),",
    "SNR": r"(SNR-S\d+\w+-\d+\w*)\s+Device",
    "DLINK": r"(D[EG]S-\d+-(\d+)[^\s]*)",
    "ELTEX": r"(MES\d+\w*)\s+(?:\w+\s+)?(\d+)-port",
}

SNR_MODEL_MAP = {
    "SNR-S2965-8T":     {"model": "SNR-S2965-8T",  "ports": "10"},
    "SNR-S2985G-24TC": {"model": "SNR-S2965-24T", "ports": "28"},
    "SNR-S2985G-48T":   {"model": "SNR-S2965-48T", "ports": "52"},
}
## Шаблон 'inventory.py'
```
# ======================
# SECURITY & AUTHENTICATION
# ======================
ADMIN_PASSWORD_SECRET = "password2026"

# ======================
# SNMP
# ======================
SNMP_COMMUNITY_RO = "public"
SNMP_PORT = 161

# ======================
# CONFIGURATION FOR OLT CLUSTER
# ======================
OLT_DEVICES = [
    {
        "host": "192.168.2.11",
        "username": "admin",
        "password": "password-2026",
        "port": 23,
        "type": "c600"
    },
    {
        "host": "192.168.2.12",
        "username": "admin",
        "password": "password",
        "port": 23,
        "type": "c300"
    },
    {
        "host": "192.168.2.13",
        "username": "admin",
        "password": "password",
        "port": 23,
        "type": "c300"
    },
    {
        "host": "192.168.2.14",
        "username": "admin",
        "password": "password",
        "port": 23,
        "type": "c300"
    },
    {
        "host": "192.168.2.16",
        "username": "admin",
        "password": "password",
        "port": 23,
        "type": "c300"
    },
    {
        "host": "192.168.2.17",
        "username": "admin",
        "password": "password",
        "port": 23,
        "type": "c300"
    },
    {
        "host": "192.168.2.18",
        "username": "admin",
        "password": "password",
        "port": 23,
        "type": "c300"
    },
    {
        "host": "192.168.2.19",
        "username": "admin",
        "password": "password",
        "port": 23,
        "type": "c300"
    }
]

# ======================
# Switches list
# ======================
SWITCH_LIST = {
    "Олимпийский": [
        {"ip": "172.31.11.150", "desc": "Махачкалинское шоссе 3 - дом 25"},
        {"ip": "172.31.11.151", "desc": "Дом 26 (пример)"}
    ],
    "Автостанция": [
        {"ip": "192.11.71.2", "desc": "Здание автовокзала"},
    ],
    "Грозненская дом 106": [
        {"ip": "192.11.71.3", "desc": "Подъезд 1"},
    ],
    "Без папки (Остальные)": [
        {"ip": "192.11.71.4", "desc": "Неизвестный адрес"},
    ]
    # Добавьте сюда остальные папки из HostMonitor...
}
```
# noc-monitor

**noc-monitor** — fullstack-система мониторинга абонентского оборудования в реальном времени. Объединяет опрос GPON OLT (ZTE) через Telnet и мониторинг коммутаторов доступа через SNMPv2 в единый интерактивный веб-интерфейс.

[![Version](https://img.shields.io/badge/Version-3.0.0-indigo.svg)](https://github.com/ZephronixQ/noc-monitor/releases)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-4.2+-FF3E00?logo=svelte&logoColor=white)](https://svelte.dev/)
[![Docker](https://img.shields.io/badge/Docker-Full%20Stack-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative&logoColor=white)](LICENSE)

---

## Возможности

- **GPON мониторинг** — отслеживание статусов ONU (LOS, DyingGasp, Offline) с автоматическим получением описаний для проблемных портов на базе оборудования ZTE C300/C320 и C600/C650.
- **Разделение аварий (LOS/LOSi)** — бэкенд автоматически определяет физический обрыв оптического кабеля (`LOS`) и затухания или отключение абонентского терминала (`LOSi`).
- **Switch мониторинг** — проверка доступности коммутаторов разных вендоров через SNMPv2 с автоматическим определением аппаратных моделей.
- **Интерактивный «Ночной аудит»** — календарная сетка инцидентов с фильтрацией по рабочим сменам и автоматическим объединением кратковременного дребезга контактов в раскрываемые кластеры.
- **Real-time дашборд** — обновление данных через WebSocket с реактивным подсчетом здоровья сети (Health Metrics) и графиками динамики аварий.
- **Экспорт CSV** — выгрузка состояния любого порта OLT в один клик.

---

## Поддерживаемое оборудование

**GPON OLT:**
- ZTE ZXA10 C300, C320, C600, C650

**Коммутаторы (SNMPv2):**
- ZTE ZXR10, SNR S2965/S2985/S2990, D-Link DES/DGS, Eltex MES

---

## Архитектура проекта

Система построена на современной асинхронной базе с разделением зон ответственности:

```
┌────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                  │
│                 Svelte (Modular Components & Stores)                   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (HTTP / WebSocket)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          NGINX REVERSE PROXY                           │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                   │
│                        FastAPI application                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │    Netmiko       │    │    PySNMP        │    │    SQLite 3      │  │
│  │ (OLT Connector)  │    │(Switch Poll Loop)│    │(Incident History)│  │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Конфигурация

Перед запуском создайте файл `backend/config/inventory.py` на основе шаблона `backend/config/inventory.md` — укажите адреса устройств, учётные данные и SNMP community.

> ⚠️ Файл с реальными данными добавлен в `.gitignore` и не публикуется в репозитории.

| Файл | Что содержит |
|---|---|
| `backend/config/inventory.py` | Списки `OLT_DEVICES` (IP, порт, тип, учетные данные), `SWITCH_LIST` (группы и IP), SNMP community |
| `backend/config/settings.py` | Интервал опроса (`POLL_INTERVAL_SEC`), число потоков (`MAX_WORKERS`), OID, паттерны вендоров |

---

## Быстрый запуск через Docker Compose

Развертывание системы со всеми зависимостями (Backend, Frontend, Nginx, SQLite Volume) выполняется одной командой:

```bash
git clone https://github.com/ZephronixQ/noc-monitor.git
cd noc-monitor
docker compose up -d --build
```

- Интерфейс доступен по адресу: `http://localhost` (или внешнему IP вашего сервера на стандартном порту `80`).
- Все запросы к API и WebSocket автоматически проксируются через Nginx.
- База данных истории инцидентов сохраняется на хост-машине в директории `./backend/data`.

Предпочитаете ручной запуск без Docker? → 📄 [docs/manual-setup.md](docs/manual-setup.md)

## Лицензия

См. файл [LICENSE](LICENSE) для информации о лицензии.
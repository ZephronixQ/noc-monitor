# noc-monitor

**noc-monitor** — fullstack-система мониторинга абонентского оборудования в реальном времени enterprise-уровня. Объединяет опрос GPON OLT (ZTE C300/C600) через Telnet и мониторинг коммутаторов доступа через SNMPv2 в единый защищенный веб-интерфейс.

[![Version](https://img.shields.io/badge/Version-4.0.0-indigo.svg)](https://github.com/ZephronixQ/noc-monitor/releases)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-4.2+-FF3E00?logo=svelte&logoColor=white)](https://svelte.dev/)
[![Docker](https://img.shields.io/badge/Docker-Full%20Stack-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Security](https://img.shields.io/badge/Security-Protected-rose.svg)](#безопасность-и-авторизация)
[![License](https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative&logoColor=white)](LICENSE)

---

## Возможности

- **GPON мониторинг** — отслеживание статусов ONU (LOS, DyingGasp, Offline) с автоматическим получением описаний и договоров для проблемных портов на базе оборудования ZTE C300/C320 и C600/C650.
- **Разделение аварий (LOS/LOSi)** — бэкенд автоматически определяет физический обрыв оптического кабеля (`LOS`) и затухания или отключение абонентского терминала (`LOSi`).
- **Switch мониторинг** — проверка доступности коммутаторов разных вендоров через SNMPv2 с автоматической классификацией аппаратных моделей (ZTE, SNR, Eltex, D-Link).
- **Серверный «Ночной аудит»** — высокопроизводительный движок `audit_engine.py` для формирования сменных отчётов (17:00–09:00 и суточных) с группировкой дребезга линий на базе данных SQLite.
- **Безопасность и контроль доступа** — авторизация по динамическому паролю смены, защита от брутфорса, бан IP-адресов, запрет DevTools/контекстного меню и скрытая панель управления сессиями операторов (`/sessions`).
- **Виджет фонового опроса (Polling HUD)** — визуальный плавающий индикатор прогресса (0–100%) при ручном запуске сканирования OLT.
- **Real-time дашборд** — обновление данных через WebSocket с реактивным подсчетом здоровья сети (Health Metrics) и моментальным предзагрузочным кэшем (0 сек задержки).

---

## Поддерживаемое оборудование

**GPON OLT:**
- ZTE ZXA10 C300, C320, C600, C650

**Коммутаторы (SNMPv2):**
- ZTE ZXR10, SNR S2965/S2985/S2990, D-Link DES/DGS, Eltex MES

---

## Архитектура проекта

```
┌────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                  │
│         Svelte 4 (Micro-components, Stores & Security Guards)          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (HTTP Bearer JWT / Protected WS)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          NGINX REVERSE PROXY                           │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                   │
│                     FastAPI Security Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │    Netmiko       │  │    PySNMP        │  │  SQLite 3 (Incidents │  │
│  │ (OLT Connector)  │  │(Switch Poll Loop)│  │  Sessions & Audit)   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘  │
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

## Безопасность и Авторизация

1. **Пароль смены:** Автоматически формируется по текущей дате (`ДДММГГГГ`).
2. **Панель Безопасности (`/sessions`):** Скрытый раздел управления активными сессиями с возможностью принудительного разрыва доступа (Session Kill), перманентного бана IP и просмотра логов аудита.
3. **Защита от брутфорса:** Блокировка IP на 24 часа после 3 неверных попыток ввода пароля смены.

---

## Быстрый запуск через Docker Compose

```bash
git clone https://github.com/ZephronixQ/noc-monitor.git
cd noc-monitor
# Создайте backend/config/inventory.py на основе шаблона
docker compose up -d --build
```

- Интерфейс доступен по адресу: `http://localhost`
- Секретная панель управления сессиями: `http://localhost/sessions`
- Все запросы к API и WebSocket автоматически проксируются через Nginx.
- База данных истории инцидентов сохраняется на хост-машине в директории `./backend/data`.

Предпочитаете ручной запуск без Docker? → 📄 [docs/manual-setup.md](docs/manual-setup.md)

## Лицензия

См. файл [LICENSE](LICENSE) для информации о лицензии.
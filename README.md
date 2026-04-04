# noc-monitor

**noc-monitor** — fullstack-система мониторинга абонентского оборудования в реальном времени. Объединяет опрос GPON OLT (ZTE) через Telnet и мониторинг коммутаторов доступа через SNMPv2 в единый интерактивный веб-интерфейс.

[![Version](https://img.shields.io/github/tag/ZephronixQ/noc-monitor.svg)](https://github.com/ZephronixQ/noc-monitor/releases)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-4.0+-FF3E00?logo=svelte&logoColor=white)](https://svelte.dev/)
[![Docker](https://img.shields.io/badge/Docker-In%20Progress-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative&logoColor=white)](LICENSE)
[![SNMP](https://img.shields.io/badge/SNMP-v2c-FF6B35?logo=cisco&logoColor=white)](https://en.wikipedia.org/wiki/Simple_Network_Management_Protocol)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20WSL-FCC624?logo=linux&logoColor=black)](https://github.com/ZephronixQ/noc-monitor)

---

## Возможности

- **GPON мониторинг** — отслеживание статусов ONU (LOS, DyingGasp, Offline) с автоматическим получением описаний для проблемных портов.
- **Switch мониторинг** — проверка доступности коммутаторов разных вендоров через SNMP.
- **Real-time дашборд** — автообновление данных через WebSocket без перезагрузки страницы.
- **Экспорт CSV** — выгрузка состояния любого порта в один клик.

---

## Поддерживаемое оборудование

**GPON OLT:**
- ZTE ZXA10 C300, C320

**Коммутаторы (SNMPv2):**
- ZTE ZXR10, SNR S2965/S2985/S2990, D-Link DES/DGS, Eltex MES

---

## Скриншоты
 
**GPON мониторинг — статусы ONU по портам OLT**
![GPON Dashboard](docs/screenshots/screen1.png)
 
**Switch мониторинг — статус узловых коммутаторов через SNMP**
![Switch Dashboard](docs/screenshots/screen2.png)

---

## Конфигурация

Перед запуском создайте файл `backend/config/inventory.py` на основе шаблона — укажите адреса устройств, учётные данные и SNMP community.

> ⚠️ Файл с реальными данными добавлен в `.gitignore` и не публикуется в репозитории.

| Файл | Что содержит |
|---|---|
| `backend/config/inventory.py` | Списки `OLT_LIST`, `SWITCH_LIST`, учётные данные, SNMP community |
| `backend/config/settings.py` | Интервал опроса (`POLL_INTERVAL_SEC`), число потоков (`MAX_WORKERS`), OID, паттерны вендоров |

---

## Запуск

```bash
git clone https://github.com/ZephronixQ/noc-monitor.git
cd noc-monitor
docker compose up --build
```

> Требуется установленный [Docker](https://docs.docker.com/get-docker/).  
> Интерфейс доступен по адресу: `http://localhost:5173`

Предпочитаете ручной запуск без Docker? → 📄 [docs/manual-setup.md](docs/manual-setup.md)

## Лицензия

См. файл [LICENSE](LICENSE) для информации о лицензии.

## Вклад

Прочитайте [CONTRIBUTING.md](CONTRIBUTING.md) для информации о том, как внести вклад в проект.

## Журнал изменений

См. файл [CHANGELOG.md](docs/CHANGELOG.md) для истории изменений.

## Список задач

См. файл [TODO.md](docs/TODO.md) для текущих задач и планов развития.

## Кодекс поведения

Участвуя в проекте, вы соглашаетесь соблюдать наш [кодекс поведения](CODE_OF_CONDUCT.md).

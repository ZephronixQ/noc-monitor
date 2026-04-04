# Changelog

Все значимые изменения проекта фиксируются в данном файле.
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

---

## [1.0.0] — 2026-04-04

Первый публичный релиз **noc-monitor** — fullstack-системы мониторинга GPON и коммутаторов.

### Backend

- FastAPI приложение с lifespan, CORS middleware и двумя endpoint'ами:
  - `GET /api/data` — первичная загрузка состояния
  - `WebSocket /ws` — live-обновления
- Асинхронный цикл опроса (`poll_devices_loop`) с интервалом 30 минут
- OLT-клиент (`olt_client.py`) на Netmiko + ThreadPoolExecutor:
  - Парсинг `show gpon onu state` (форматы A и B)
  - Автоматическое получение Description для ONU в статусах LOS / DyingGasp / Offline
- SNMP-клиент (`snmp_client.py`) на PySNMP asyncio:
  - GET `sysDescr` с timeout 2 с и 1 retry
  - Парсинг вендоров: ZTE ZXR10, SNR S-серии, D-Link DES/DGS, Eltex MES
- Парсеры (`utils/parser.py`):
  - `parse_onu_line` — разбор строк CLI ZTE OLT
  - `parse_sys_descr` — определение вендора и модели коммутатора по sysDescr
- WebSocket менеджер (`ws_manager.py`) с broadcast по всем активным соединениям
- Раздельные конфиги: `inventory.py` (оборудование, credentials) и `settings.py` (параметры, OID, паттерны)

### Frontend

- Svelte + Vite + Tailwind CSS
- Подключение к backend через REST (первичная загрузка) и WebSocket (live-обновления)
- Карточки устройств с цветными индикаторами статуса и счётчиками ONU
- Раскрывающиеся порты с фильтрацией по статусу (All / working / LOS / DyingGasp / Offline)
- Глобальный фильтр «Только аварийные» и поиск по интерфейсу / договору
- Пагинация: 16 портов на страницу, 50 ONU на страницу
- Экспорт состояния порта в CSV
- Таймер обратного отсчёта до следующего опроса
- Тёмная / светлая тема
- Toast-уведомления об обновлениях и ошибках
- Звуковые алерты при появлении аварий (Web Audio API)
- Метрики текущего устройства: всего / в работе / LOS / DyingGasp
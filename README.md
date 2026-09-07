# noc-monitor v5.0.0 Enterprise

**noc-monitor** — fullstack-система оперативного мониторинга и аудита сетевой инфраструктуры интернет-провайдера (ISP/NOC). Система объединяет низкоуровневый опрос GPON OLT (ZTE C300/C320/C600/C650) по Telnet/CLI, гибридный мониторинг L2/L3-коммутаторов доступа (SNMPv2 + ICMP Ping fallback), реляционную модель инвентаря на Django ORM и реактивный веб-интерфейс реального времени на Svelte.

[![Version](https://img.shields.io/badge/Version-5.0.0-indigo.svg)](https://github.com/ZephronixQ/noc-monitor/releases)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-4.2+-FF3E00?logo=svelte&logoColor=white)](https://svelte.dev/)
[![Docker](https://img.shields.io/badge/Docker-Full%20Stack-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative&logoColor=white)](LICENSE)

---

## Демонстрация интерфейса

<div align="center">
  <img width="1919" height="1079" alt="Image" src="https://github.com/user-attachments/assets/3e4d25e9-02ed-46bf-9d23-8935dbe900cb" />
</div>

---

## Ключевые возможности v5.0.0

- **Инвентарь на Django Admin:** Управление OLT-станциями, кластерами (домами/районами) и коммутаторами доступа через встроенный интерфейс `/admin/` с валидацией моделей и поддержкой горячего включения/отключения устройств (`is_active`).
- **Гибридный опрос L2 (SNMP + Ping fallback):** Если коммутатор не отвечает по SNMP, система автоматически проверяет доступность хоста через ICMP Ping и выставляет соответствующий бейдж в UI, исключая ложные срабатывания.
- **Глубокий анализ GPON (ZTE C300/C600):** Разделение обрыва оптической магистрали (`LOS`), изгиба/затухания патчкорда (`LOSi`), проблем с питанием (`DyingGasp`) и плановых отключений (`Offline`).
- **Сплит-консоль инцидентов (3/10 + 7/10):** Левый блок с круговым датчиком доступности и спектром распределения потерь; правый блок с синхронизированной матрицей реагирования по типам оборудования.
- **Серверный движок аудита и флаппинга:** Интеллектуальное объединение частых падений одного узла за 60 минут в единый инцидент с разворачиваемой хронологией микро-сбоев.
- **Годовые авторизационные токены:** Полноценная аутентификация операторов по учётным записям Django с выпуском подписанного JWT-токена сроком действия 365 дней.
- **Архитектура единого порта (80/443):** Nginx выступает фронтенд-прокси для сборки Svelte, API FastAPI, WebSocket и панели Django Admin без проблем с CORS и портами.

---

## Архитектура системы

```
┌────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                  │
│         Svelte 4 + TailwindCSS + Stores (Dark/Light Responsive)        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (HTTP / WebSocket / Bearer JWT)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          NGINX REVERSE PROXY                           │
│     / -> Web UI | /api/ -> FastAPI | /ws -> WS | /admin/ -> Django     │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                   │
│        FastAPI (Async I/O Engine) + WSGIMiddleware (Django Core)       │
│                                                                        │
│  ┌───────────────────────┐ ┌──────────────────┐ ┌───────────────────┐  │
│  │   Django ORM Models   │ │  PySNMP + ICMP   │ │   Netmiko Telnet  │  │
│  │ (Inventory/Incidents) │ │ (L2/L3 Poller)   │ │   (ZTE C300/C600) │  │
│  └───────────────────────┘ └──────────────────┘ └───────────────────┘  │
│                                  │                                     │
│                                  ▼                                     │
│                       SQLite 3 (WAL-режим)                             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Быстрый запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/ZephronixQ/noc-monitor.git
cd noc-monitor
```

### 2. Настройка переменных окружения
Скопируйте конфигурационный файл и настройте параметры под вашу сеть:
```bash
cp backend/.env.example backend/.env
```

Содержимое `backend/.env`:
```ini
SNMP_COMMUNITY=public
SNMP_PORT=161

DJANGO_ADMIN_USER=admin
DJANGO_ADMIN_PASSWORD=your_secure_password
DJANGO_SECRET_KEY=generate_random_secret_key_here
```

### 3. Запуск контейнеров
```bash
docker compose up -d --build
```

После завершения сборки:
- **Основной интерфейс мониторинга:** `http://localhost`
- **Панель управления сетевым оборудованием:** `http://localhost/admin`
- Учётные данные по умолчанию: логин и пароль из вашего файла `.env` (при первом запуске создаются автоматически).

---

## Конфигурация через Django Admin

В версии 5.0.0 статический файл `inventory.py` упразднён. Всё управление сетевым парком перенесено в базу данных:

1. Перейдите по адресу `http://localhost/admin`.
2. Авторизуйтесь под администратором.
3. Добавьте:
   - **Локации / Папки (Clusters):** Районы, дома, оптические узлы.
   - **Коммутаторы (Switches):** IP, описание, привязка к локации, принудительное переопределение модели при необходимости.
   - **Станции OLT (OltDevice):** IP, логин/пароль Telnet, тип шасси (`ZTE C300/C320` или `ZTE C600/C650`).

Система автоматически подхватит изменения в следующем цикле опроса без перезагрузки бэкенда.

---

## Управление контейнерами

```bash
# Просмотр логов опроса сети в реальном времени
docker logs -f noc-backend

# Перезапуск сервисов
docker compose restart

# Остановка с сохранением базы данных
docker compose down

# Сброс и чистая пересборка
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## Лицензия

Проект распространяется под лицензией [MIT](LICENSE).

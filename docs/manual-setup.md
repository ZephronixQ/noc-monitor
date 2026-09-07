# Запуск noc-monitor v5.0.0

> Поддерживаются два режима запуска: **Docker Compose** (основной для продакшна) и **ручной запуск** (для локальной разработки).  
> Актуально для **Windows 11 (WSL2 Debian/Ubuntu)** и **серверов Linux (Debian 12/13, Ubuntu 22.04/24.04)**.

---

## Содержание

- [1. Подготовка окружения (только для Windows WSL)](#1-подготовка-окружения-только-для-windows-wsl)
- [2. Системные пакеты и зависимости](#2-системные-пакеты-и-зависимости)
- [3. Настройка MIB-файлов (SNMP)](#3-настройка-mib-файлов-snmp)
- [4. Клонирование и настройка конфигурации (.env)](#4-клонирование-и-настройка-конфигурации-env)
- [🐳 Запуск через Docker Compose (Рекомендуется)](#-запуск-через-docker-compose-рекомендуется)
- [⚙️ Ручной запуск для разработки](#️-ручной-запуск-для-разработки)
- [Наполнение инвентаря через Django Admin](#наполнение-инвентаря-через-django-admin)
- [Диагностика и решение проблем](#диагностика-и-решение-проблем)

---

## 1. Подготовка окружения (только для Windows WSL)

Откройте PowerShell **от имени администратора**:

```powershell
wsl --install Debian
```

> ⚠️ После установки перезагрузите компьютер и войдите в WSL:

```powershell
wsl
```

---

## 2. Системные пакеты и зависимости

Выполните установку базовых утилит и пакетов для сборки:

```bash
sudo apt update
sudo apt install -y snmp wget git python3-venv python3-pip nodejs npm iputils-ping
```

---

## 3. Настройка MIB-файлов (SNMP)

### 3.1 Установка через пакетный менеджер

```bash
sudo apt install -y snmp-mibs-downloader
sudo download-mibs
```

> ⚠️ Если в репозитории Debian пакета нет, включите компоненты `contrib` и `non-free`:

```bash
sudo sed -i 's/main/main contrib non-free non-free-firmware/' /etc/apt/sources.list
sudo apt update
sudo apt install -y snmp-mibs-downloader
```

### 3.2 Создание конфигурационного файла SNMP

```bash
mkdir -p ~/.snmp
echo "mibs +ALL" >> ~/.snmp/snmp.conf
```

### 3.3 Ручная загрузка MIB-файлов (если пакет недоступен)

```bash
cd /usr/share/snmp/mibs

sudo wget -q https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/SNMPv2-SMI.txt
sudo wget -q https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/SNMPv2-TC.txt
sudo wget -q https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/SNMPv2-CONF.txt
sudo wget -q https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/SNMPv2-MIB.txt
sudo wget -q https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/RFC1213-MIB.txt
sudo wget -q https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/IF-MIB.txt
sudo wget -q https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/SNMP-FRAMEWORK-MIB.txt
sudo wget -q https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/SNMP-VIEW-BASED-ACM-MIB.txt
sudo wget -q https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/INET-ADDRESS-MIB.txt
```

### 3.4 Проверка работы SNMP

```bash
snmpwalk -v2c -c public <IP_КОММУТАТОРА> sysDescr
```

---

## 4. Клонирование и настройка конфигурации (.env)

Клонируйте репозиторий в рабочую директорию:

```bash
cd /opt
sudo git clone https://github.com/ZephronixQ/noc-monitor.git
sudo chown -R $USER:$USER /opt/noc-monitor
cd /opt/noc-monitor
```

Создайте рабочий файл переменных окружения:

```bash
cp backend/.env.example backend/.env
```

Отредактируйте параметры в `backend/.env`:

```ini
# SNMP параметры опроса по умолчанию
SNMP_COMMUNITY=public
SNMP_PORT=161

# Учетные данные суперпользователя Django (создается автоматически)
DJANGO_ADMIN_USER=admin
DJANGO_ADMIN_PASSWORD=change_this_password_2026

# Секретный ключ подписи Django и JWT-токенов
DJANGO_SECRET_KEY=k8f#m2@9!x_generate_random_secret_key_here
```

> ⚠️ В версии **v5.0.0** статический файл `inventory.py` больше не используется. Все устройства добавляются через базу данных и панель Django Admin.

---

## 🐳 Запуск через Docker Compose (Рекомендуется)

Docker-сборка изолирует все компоненты, запускает ASGI-сервер бэкенда, собирает клиентский Svelte-код и конфигурирует Nginx в качестве единого reverse proxy на 80 порту.

### Включение Systemd в WSL (для Windows)

```bash
sudo nano /etc/wsl.conf
```

Вставьте блок:

```ini
[boot]
systemd=true
```

Сохраните изменения (`Ctrl+O`, `Enter`, `Ctrl+X`) и перезапустите WSL из PowerShell (от имени администратора):

```powershell
wsl --shutdown
```

### Установка Docker в Debian/Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

### Сборка и запуск контейнеров

```bash
cd /opt/noc-monitor
docker compose up -d --build
```

При старте контейнер `noc-backend`:
1. Автоматически применит все миграции Django в базу `./backend/data/noc_database.sqlite3`.
2. Создаст суперпользователя `admin` с паролем из файла `.env`.
3. Запустит фоновые циклы опроса коммутаторов и станций OLT.

Проверьте статус контейнеров:

```bash
docker compose ps
```

Ожидаемый результат:

```text
NAME           IMAGE                  COMMAND                  SERVICE    STATUS      PORTS
noc-backend    noc-monitor-backend    "sh -c 'python manag…"   backend    running     8000/tcp
noc-frontend   noc-monitor-frontend   "/docker-entrypoint.…"   frontend   running     0.0.0.0:80->80/tcp
```

* **Веб-интерфейс мониторинга:** `http://localhost`
* **Панель управления инвентарем:** `http://localhost/admin`

---

## ⚙️ Ручной запуск для разработки

Используется для внесения правок в код без необходимости пересобирать Docker-образы.

### 1. Запуск Backend

```bash
cd /opt/noc-monitor/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Создание структуры БД и миграции
python manage.py migrate

# Создание суперпользователя вручную
python manage.py createsuperuser

# Запуск единого ASGI-сервера
python -m uvicorn noc_project.asgi:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Запуск Frontend

В отдельном окне терминала:

```bash
cd /opt/noc-monitor/frontend
npm install
npm run dev
```

Интерфейс разработчика будет доступен по адресу: `http://localhost:5173`.

---

## Наполнение инвентаря через Django Admin

После первого запуска система готова к внесению оборудования:

1. Откройте в браузере: `http://localhost/admin`
2. Войдите под учетной записью администратора (`admin` и пароль из `.env`).
3. Заполните сущности:
   * **Локации / Папки (`Clusters`):** Добавьте группы (например: `Мкр. Центральный`, `Дом 14`, `Северный узел`).
   * **Коммутаторы (`Switches`):** Добавьте устройства, укажите IP, текстовое описание (адрес/подъезд), выберите локацию. При необходимости укажите модель в поле `model_override`.
   * **Станции OLT (`Olt Devices`):** Укажите IP станции, порт (по умолчанию `23`), реквизиты доступа Telnet и выберите архитектуру шасси (`ZTE C300/C320` или `ZTE C600/C650`).

> ℹ️ Поллеры автоматически подхватывают добавленные и измененные устройства в реальном времени без перезапуска сервисов.

---

## Диагностика и решение проблем

### Просмотр логов в реальном времени

```bash
# Логи бэкенда и фоновых поллеров (SNMP, Telnet, Django)
docker logs -f noc-backend

# Логи веб-сервера Nginx
docker logs -f noc-frontend
```

### Ошибка 401 Unauthorized в интерфейсе

Сессия оператора хранится в LocalStorage в течение 365 дней. Если вы изменили ключ `DJANGO_SECRET_KEY` в `.env`, существующие токены станут недействительными:
1. Выполните логаут через правый верхний угол интерфейса (иконка выхода).
2. Авторизуйтесь заново под учетной записью из Django Admin.

### Пересоздание контейнеров с нуля с сохранением истории

База данных и инвентарь хранятся на хосте в папке `./backend/data`. Вы можете безопасно пересобирать образы:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```
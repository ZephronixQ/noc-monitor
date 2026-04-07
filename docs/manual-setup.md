# Запуск noc-monitor

> Поддерживаются два режима запуска: **Docker** (рекомендуется) и **ручной**.  
> Актуально для **Windows 11 WSL** и **Linux Debian/Ubuntu**.

---

## Содержание

- [1. Установка WSL и Debian (только для Windows)](#1-установка-wsl-и-debian-только-для-windows)
- [2. Подготовка системы](#2-подготовка-системы)
- [3. Настройка MIB-файлов (SNMP)](#3-настройка-mib-файлов-snmp)
- [4. Клонирование и конфигурация](#4-клонирование-и-конфигурация)
- [🐳 Запуск через Docker (рекомендуется)](#-запуск-через-docker-рекомендуется)
- [⚙️ Ручной запуск](#️-ручной-запуск)
- [Замечания](#замечания)

---

## 1. Установка WSL и Debian (только для Windows)

Откройте PowerShell **от имени администратора**:

```powershell
wsl --install Debian
```

> ⚠️ После установки потребуется перезагрузка. Затем запустите WSL:

```powershell
wsl
```

---

## 2. Подготовка системы

```bash
sudo apt update
sudo apt install -y snmp wget git python3-venv
```

---

## 3. Настройка MIB-файлов (SNMP)

### 3.1 Установка через пакетный менеджер

```bash
sudo apt install snmp-mibs-downloader
sudo download-mibs
```

> ⚠️ На Debian 13 (trixie) пакет может отсутствовать — выполните шаг 3.2.

### 3.2 Если пакет недоступен — добавьте репозиторий non-free

```bash
sudo sed -i 's/main/main contrib non-free non-free-firmware/' /etc/apt/sources.list
sudo apt update
sudo apt install snmp-mibs-downloader
```

### 3.3 Создать конфиг SNMP

```bash
mkdir -p ~/.snmp
echo "mibs +ALL" >> ~/.snmp/snmp.conf
```

### 3.4 Если пакет так и не установился — скачать MIB-файлы вручную

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

### 3.5 Исправить битый файл SNMPv2-PDU

```bash
sudo rm /usr/share/snmp/mibs/ietf/SNMPv2-PDU
sudo wget -q -O /usr/share/snmp/mibs/ietf/SNMPv2-PDU \
  https://raw.githubusercontent.com/net-snmp/net-snmp/master/mibs/SNMPv2-PDU.txt
```

### 3.6 Проверка SNMP

```bash
snmpwalk -v2c -c public <IP> sysDescr
snmpget -v2c -c public <IP> IF-MIB::ifOperStatus.2
```

---

## 4. Клонирование и конфигурация

```bash
git clone https://github.com/ZephronixQ/noc-monitor.git
cd noc-monitor
```

Создайте файл `backend/config/inventory.py` и укажите в нём адреса устройств, учётные данные и SNMP community:

```python
# Список OLT (ZTE)
OLT_LIST = ["192.168.1.10", "192.168.1.11"]

# Список коммутаторов (SNMP)
SWITCH_LIST = ["192.168.1.20", "192.168.1.21"]

# Учётные данные OLT
DEFAULT_USER = "admin"
DEFAULT_PASS = "password"

# SNMP
SNMP_COMMUNITY_RO = "public"
SNMP_PORT = 161
```

> ⚠️ Файл с реальными данными добавлен в `.gitignore` и не публикуется в репозитории.

При необходимости скорректируйте параметры опроса в `backend/config/settings.py`:

```python
MAX_WORKERS = 10          # Число параллельных Telnet-потоков
POLL_INTERVAL_SEC = 1800  # Интервал опроса (секунды), по умолчанию 30 минут
```

---

## 🐳 Запуск через Docker (рекомендуется)

Docker-режим не требует ручной установки Python, Node.js и зависимостей. Всё запускается в изолированных контейнерах и поднимается автоматически при старте Windows.

### Включить Systemd в WSL

Без этого Docker не запустится автоматически при старте WSL:

```bash
sudo nano /etc/wsl.conf
```

Вставить:

```ini
[boot]
systemd=true
```

Сохранить (`Ctrl+O`, `Enter`, `Ctrl+X`), перезапустить WSL из PowerShell (от администратора):

```powershell
wsl --shutdown
```

### Установка Docker в Debian

> Не устанавливайте Docker Desktop для Windows — используйте нативный Docker внутри WSL/Debian.

```bash
# Удалить старые версии (если были)
sudo apt-get remove docker docker-engine docker.io containerd runc

# Установить зависимости и добавить репозиторий Docker
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установить Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Добавить в автозагрузку внутри Debian
sudo systemctl enable docker

# Добавить текущего пользователя в группу docker (чтобы не писать sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### Развернуть проект

Проект должен находиться в Linux-файловой системе, а не на Windows-диске (`/mnt/c/...`) — иначе Docker работает нестабильно из-за различий в правах доступа.

```bash
# Создать директорию в Linux-файловой системе
sudo mkdir -p /opt/noc-monitor
sudo chown $USER:$USER /opt/noc-monitor

# Определение пути нынешнего проекта 'noc-monitor'
pwd

# Скопировать файлы (если проект лежит на Windows-диске)
cp -r /mnt/c/Users/USER/noc-monitor/* /opt/noc-monitor/

cd /opt/noc-monitor

# Собрать и запустить контейнеры
docker compose up -d --build
```

> ⏳ Первая сборка занимает 15–20 минут — Docker скачивает образы и компилирует зависимости. Последующие запуски занимают несколько секунд благодаря кэшу слоёв.

Проверить состояние контейнеров:

```bash
docker ps
```

Ожидаемый вывод:

```
CONTAINER ID   NAME           STATUS         PORTS
xxxxxxxxxxxx   noc-frontend   Up X minutes   0.0.0.0:80->80/tcp
xxxxxxxxxxxx   noc-backend    Up X minutes   0.0.0.0:8000->8000/tcp
```

Интерфейс доступен по адресу: **http://localhost**

### Автозапуск вместе с Windows

Открой **PowerShell от имени администратора** и выполни:
```powershell
$trigger1 = New-ScheduledTaskTrigger -AtStartup
$trigger1.Delay = "PT10S"

$trigger2 = New-ScheduledTaskTrigger -AtStartup
$trigger2.Delay = "PT30S"

# Задача 1: удерживает WSL живым в фоне (запускается через 10 сек после старта)
$action1 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-WindowStyle Hidden -Command "wsl -d Debian -u root -e bash -c ''while true; do sleep 60; done''"'
Register-ScheduledTask -TaskName "WSL_KeepAlive" -Action $action1 -Trigger $trigger1 -Settings (New-ScheduledTaskSettingsSet -Hidden -ExecutionTimeLimit 0) -RunLevel Highest -User "$env:USERDOMAIN\$env:USERNAME"

# Задача 2: запуск Docker (запускается через 30 сек, когда WSL уже живой)
$action2 = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-WindowStyle Hidden -Command "wsl -d Debian -u root -e bash -c ''service docker start && cd /opt/noc-monitor && docker compose up -d''"'
Register-ScheduledTask -TaskName "NOC_Autostart" -Action $action2 -Trigger $trigger2 -Settings (New-ScheduledTaskSettingsSet -Hidden) -RunLevel Highest -User "$env:USERDOMAIN\$env:USERNAME"
```

Проверить созданные задачи:
```powershell
Get-ScheduledTask -TaskName "NOC_Autostart"
Get-ScheduledTask -TaskName "WSL_KeepAlive"
```

### Управление контейнерами

```bash
# Перезапустить после изменений в коде
docker compose up -d --build

# Пересобрать только один сервис
docker compose up -d --build backend

# Остановить всё
docker compose down

# Пересобрать без кэша (если изменения не применяются)
docker compose down
docker compose build --no-cache backend
docker compose up -d

# Применить изменение в одном файле без пересборки
docker cp backend/network/olt_client.py noc-backend:/app/backend/network/olt_client.py
docker restart noc-backend

# Логи в реальном времени
docker compose logs -f
docker logs noc-backend
docker logs noc-frontend
```

---

## ⚙️ Ручной запуск

Альтернатива Docker — запуск напрямую через Python и Node.js. Удобно для разработки.

### Запуск Backend

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 backend/main.py
```

### Запуск Frontend

```bash
cd frontend
npm install
npm run dev
```

Интерфейс доступен по адресу: `http://localhost:5173`

---

## Замечания

- `public` — только чтение (RO)
- При `Timeout` во время SNMP-опроса — проверьте community-строку в `inventory.py`
- Не отключайте порт, через который идёт SNMP-опрос — устройство перестанет отвечать
- На Debian 13 (trixie) `snmp-mibs-downloader` может отсутствовать — используйте раздел 3.4
- Проект должен лежать в `/opt/noc-monitor`, а не в `/mnt/c/` — Docker работает нестабильно с Windows-дисками

---

*Протестировано на Windows 11 + WSL + Debian GNU/Linux 13 (trixie) — 07.04.2026*
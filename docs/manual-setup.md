# Ручной запуск noc-monitor

> Альтернатива Docker — полная настройка окружения вручную.  
> Актуально для **Windows 11 WSL** и **Linux Debian/Ubuntu**.

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

## 5. Запуск Backend

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 backend/main.py
```

---

## 6. Запуск Frontend

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

---

*Протестировано на Windows 11 + WSL + Debian GNU/Linux 13 (trixie) — 04.04.2026*
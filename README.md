# 📡 MiniNOC – AI Network Health Monitoring Dashboard

MiniNOC is a lightweight **Network Operations Center (NOC)** style monitoring tool built using **Python + Flask**.
It continuously monitors network devices using **ICMP ping**, displays real-time status on a **web dashboard**,
and sends **Telegram alerts** when a device goes DOWN or recovers.

---

## 🔥 Features

- ✅ Live device monitoring (UP / DOWN / UNKNOWN)
- 📊 Real-time dashboard with charts
- 🔁 Background monitoring every 30 seconds
- 🧾 Device inventory using YAML
- ➕ Add / ➖ Delete devices via web UI
- 🔔 Telegram alerts for DOWN & RECOVERY
- 💻 Works on Windows / Linux / Kali Linux

---

## 🧱 Project Structure

```
MININOC/
│
├── .env
├── devices.yaml
├── mininoc.log
├── monitor_core.py
├── web_app.py
│
├── templates/
│   ├── dashboard.html
│   ├── devices.html
│
└── __pycache__/
```

---

## ⚙️ Requirements

### 🐍 Python
- Python **3.10 or higher** (Tested on Python 3.13)

### 📦 Python Packages

Create `requirements.txt` with:
```
flask
pyyaml
python-dotenv
requests
```

Install:
```
pip install -r requirements.txt
```

---

## 🔐 Telegram Bot Setup (Optional)

### Step 1: Create Bot
- Open Telegram
- Search **@BotFather**
- Create bot and copy **BOT TOKEN**

### Step 2: Get Chat ID
- Send message to your bot
- Use chat-id finder bot or Telegram API

### Step 3: Create `.env` file

```
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
```

If `.env` is missing, project still runs without Telegram alerts.

---

## 🖥️ Device Configuration (`devices.yaml`)

Example:
```yaml
devices:
- name: Router1
  ip: 192.168.58.10
  enabled: true
  ssh_enabled: true
  ssh_user: admin
  ssh_port: 22
  telnet_enabled: true
  telnet_port: 23
```

### Fields Explanation

| Field | Description |
|-----|------------|
| name | Device name |
| ip | Device IP |
| enabled | Enable monitoring |
| ssh_enabled | SSH helper |
| telnet_enabled | Telnet helper |

---

## 🧠 How Monitoring Works

File: `monitor_core.py`

1. Loads devices from `devices.yaml`
2. Runs background thread every 30 seconds
3. Uses OS ping command
4. Detects status change
5. Sends Telegram alerts

---

## 🌐 Web Application

File: `web_app.py`

### Routes

| Route | Purpose |
|------|--------|
| / | Dashboard |
| /api/status | JSON API |
| /devices | Device management |

Monitoring runs in background daemon thread.

---

## 📊 Dashboard

File: `templates/dashboard.html`

- Live polling every 5 seconds
- Network health gauge
- Incident view
- Availability percentage

---

## 🧾 Device Management

File: `templates/devices.html`

- View devices
- Add new devices
- Delete devices
- Updates without restart

---

## ▶️ Run Project (Step-by-Step)

### 1️⃣ Clone Repo
```
git clone https://github.com/YOUR_USERNAME/MININOC.git
cd MININOC
```

### 2️⃣ Install Requirements
```
pip install -r requirements.txt
```

### 3️⃣ Configure Telegram (Optional)
Create `.env` file

### 4️⃣ Start App
```
python web_app.py
```

### 5️⃣ Open Browser
```
http://localhost:5000
```

---

## 📜 Logs

All logs stored in:
```
mininoc.log
```

---

## 🚫 Important Notes

- Do NOT commit `.env`
- Add `.env` and `__pycache__/` to `.gitignore`
- ICMP ping must be allowed

---

## 🚀 Future Improvements

- SNMP monitoring
- Database storage
- Authentication
- Docker support

---

## 👨‍💻 Author

**Faraj**
MiniNOC – Network Health Monitoring Project

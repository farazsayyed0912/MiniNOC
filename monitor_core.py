import os
import platform
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, List

import yaml
from dotenv import load_dotenv
import requests

POLL_INTERVAL_SECONDS = 1  # background thread kitne second me ek cycle karega


# ---------------- TELEGRAM SETUP ---------------- #

load_dotenv()  # .env load karega (same folder me hona chahiye)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(text: str):
    """
    Telegram alert bhejne ka function.
    Agar token ya chat_id missing ho to quietly skip karega.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        # Config nahi hai: alert skip
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        # Agar Telegram fail bhi ho, tool crash nahi hona chahiye
        print(f"[WARN] Telegram send failed: {e}")


# ---------------- YAML LOADER (startup only) ---------------- #

def load_devices(yaml_path: str = "devices.yaml") -> List[Dict[str, Any]]:
    """
    devices.yaml file se devices list load karega.
    Ye function ab sirf startup ke time use hoga, baad me
    web_app devices_config ko runtime me update karega.
    """
    if not os.path.exists(yaml_path):
        return []

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f) or {}

    devices = data.get("devices", [])
    return [d for d in devices if d.get("enabled", True)]


# ---------------- PING FUNCTION ---------------- #

def ping_device(ip: str, count: int = 1, timeout: int = 1) -> bool:
    """
    OS ke ping command se device UP/DOWN check karega.
    True = UP, False = DOWN
    """
    system = platform.system().lower()

    if system == "windows":
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), ip]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(timeout), ip]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False


# ---------------- MAIN MONITOR LOOP ---------------- #

def monitor_loop(devices_config: List[Dict[str, Any]],
                 status_store: Dict[str, Dict[str, Any]]):
    """
    Background thread:
    - devices_config list ke current content ko har cycle me use karega
    - har device ko ping karke status_store update karega
    - agar koi device list se delete ho gaya to status_store se bhi hata dega

    devices_config ko web_app runtime me modify karega (add/delete).
    """

    while True:
        cycle_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Snapshot bana lo: agar beech me list change ho jaye to crash na ho
        devices_snapshot = list(devices_config)

        current_ips = set()

        for dev in devices_snapshot:
            name = dev.get("name", "Unknown")
            ip = dev.get("ip")
            if not ip:
                continue

            current_ips.add(ip)

            is_up = ping_device(ip)
            new_status = "UP" if is_up else "DOWN"

            record = status_store.get(ip)
            if not record:
                # First time record create
                record = {
                    "name": name,
                    "ip": ip,
                    "status": "UNKNOWN",
                    "last_change": cycle_time,
                    "last_checked": cycle_time,
                    "ssh_enabled": dev.get("ssh_enabled", False),
                    "ssh_user": dev.get("ssh_user", ""),
                    "ssh_port": dev.get("ssh_port", 22),
                    "telnet_enabled": dev.get("telnet_enabled", False),
                    "telnet_port": dev.get("telnet_port", 23),
                }

            old_status = record["status"]

            # timestamps update
            record["last_checked"] = cycle_time

            if new_status != old_status:
                record["status"] = new_status
                record["last_change"] = cycle_time
            else:
                record["status"] = new_status

            # Config fields update (agar GUI se change hua ho)
            record["ssh_enabled"] = dev.get("ssh_enabled", False)
            record["ssh_user"] = dev.get("ssh_user", "")
            record["ssh_port"] = dev.get("ssh_port", 22)
            record["telnet_enabled"] = dev.get("telnet_enabled", False)
            record["telnet_port"] = dev.get("telnet_port", 23)

            status_store[ip] = record

            # --------- STATUS CHANGE ALERT LOGIC --------- #
            if old_status in ("UP", "DOWN") and new_status != old_status:
                if new_status == "DOWN":
                    msg = (
                        f"🚨 *NETWORK ALERT*\n"
                        f"Device: *{name}*\n"
                        f"IP: `{ip}`\n"
                        f"Status: *DOWN*\n"
                        f"Time: {cycle_time}"
                    )
                    send_telegram_message(msg)
                elif new_status == "UP":
                    msg = (
                        f"✅ *RECOVERY*\n"
                        f"Device: *{name}*\n"
                        f"IP: `{ip}`\n"
                        f"Status: *UP again*\n"
                        f"Time: {cycle_time}"
                    )
                    send_telegram_message(msg)

        # Deleted devices clean-up:
        for ip in list(status_store.keys()):
            if ip not in current_ips:
                status_store.pop(ip, None)

        time.sleep(POLL_INTERVAL_SECONDS)

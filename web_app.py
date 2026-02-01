from flask import Flask, render_template, jsonify, request
from threading import Thread
from datetime import datetime
import os
import yaml

from monitor_core import load_devices, monitor_loop

app = Flask(__name__)

# Global shared structures
status_store = {}        # ip -> status info
devices_config = []      # list[dict] – runtime me modify hoga

DEVICES_YAML_PATH = "devices.yaml"


# ------------------ Helper: Load & Save devices.yaml ------------------ #

def read_devices_yaml():
    """devices.yaml ko read karke list return karega."""
    if not os.path.exists(DEVICES_YAML_PATH):
        return []
    with open(DEVICES_YAML_PATH, "r") as f:
        data = yaml.safe_load(f) or {}
    return data.get("devices", [])


def write_devices_yaml(devices_list):
    """devices.yaml ko overwrite karega diya gaya devices_list se."""
    data = {"devices": devices_list}
    with open(DEVICES_YAML_PATH, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def sync_devices_config_from_yaml():
    """
    YAML se list load karo aur global devices_config ko update karo.
    devices_config list ko inplace update karte hain, taki monitor thread
    ko same object ka reference milta rahe.
    """
    global devices_config
    devices = read_devices_yaml()
    # enabled == True walon ka hi monitor kare
    devices_enabled = [d for d in devices if d.get("enabled", True)]
    devices_config[:] = devices_enabled  # inplace replace
    return devices


# ------------------ Flask Routes ------------------ #

@app.route("/")
def dashboard():
    """Main health dashboard."""
    devices = sorted(status_store.values(), key=lambda d: d["ip"])
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("dashboard.html", devices=devices, generated_at=generated_at)


@app.route("/api/status")
def api_status():
    """JSON status API (future use)."""
    devices = sorted(status_store.values(), key=lambda d: d["ip"])
    return jsonify({"devices": devices})


@app.route("/devices", methods=["GET", "POST"])
def devices_page():
    """
    Devices management GUI:
    - GET: current devices list show
    - POST:
        form_type == add    -> add new device
        form_type == delete -> delete device by IP
    """
    message = None

    if request.method == "POST":
        form_type = request.form.get("form_type", "add")

        if form_type == "add":
            name = request.form.get("name", "").strip()
            ip = request.form.get("ip", "").strip()
            enabled = request.form.get("enabled") == "on"

            ssh_enabled = request.form.get("ssh_enabled") == "on"
            ssh_user = request.form.get("ssh_user", "").strip()
            ssh_port = request.form.get("ssh_port", "22").strip()

            telnet_enabled = request.form.get("telnet_enabled") == "on"
            telnet_port = request.form.get("telnet_port", "23").strip()

            if not name or not ip:
                message = "Name and IP are required."
            else:
                devices = read_devices_yaml()

                new_device = {
                    "name": name,
                    "ip": ip,
                    "enabled": enabled,
                    "ssh_enabled": ssh_enabled,
                    "ssh_user": ssh_user,
                    "ssh_port": int(ssh_port) if ssh_port.isdigit() else 22,
                    "telnet_enabled": telnet_enabled,
                    "telnet_port": int(telnet_port) if telnet_port.isdigit() else 23,
                }

                devices.append(new_device)
                write_devices_yaml(devices)

                # Runtime config update
                sync_devices_config_from_yaml()

                message = "Device added successfully. Monitoring will start in next cycle."

        elif form_type == "delete":
            ip_to_delete = request.form.get("ip", "").strip()
            devices = read_devices_yaml()
            # YAML se hatao
            devices = [d for d in devices if d.get("ip") != ip_to_delete]
            write_devices_yaml(devices)
            # Runtime config update
            sync_devices_config_from_yaml()
            # Status store se bhi hatao
            if ip_to_delete in status_store:
                status_store.pop(ip_to_delete, None)
            message = f"Device {ip_to_delete} removed."

    # Latest devices list for table
    devices = read_devices_yaml()
    return render_template("devices.html", devices=devices, message=message)


# ------------------ Monitor Thread Starter ------------------ #

def start_monitor_thread():
    # YAML se initial load
    sync_devices_config_from_yaml()
    t = Thread(target=monitor_loop, args=(devices_config, status_store), daemon=True)
    t.start()


if __name__ == "__main__":
    start_monitor_thread()
    app.run(host="0.0.0.0", port=5000, debug=True)

import os
import json
import time
import uuid
import requests
import webbrowser
import ctypes
import psutil
from logger import setup_logger

logger = setup_logger("agent_backend")

# Default server URL - can be overridden in config
DEFAULT_SERVER_URL = "http://192.168.1.108"

APP_DIR = os.path.join(os.getenv("APPDATA"), "ControlIt")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")

# -------------------------
# Utilities
# -------------------------

def load_config():
    defaults = {"server_url": DEFAULT_SERVER_URL}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            loaded = json.load(f)
            defaults.update(loaded)
    return defaults

def save_config(data):
    os.makedirs(APP_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# -------------------------
# Agent Registration
# -------------------------

def generate_agent_id():
    return str(uuid.uuid4())

def open_browser_for_link(agent_id, server_url):
    url = f"{server_url}/login/agent/link?agent_id={agent_id}"
    logger.debug("[INFO] Opening browser for linking")
    webbrowser.open(url)

def wait_for_link(agent_id, server_url):
    logger.debug("[INFO] Waiting for agent to be linked...")
    while True:
        try:
            res = requests.get(
                f"{server_url}/api/agent/status/{agent_id}",
                timeout=5
            )
            if res.status_code == 200 and res.json().get("linked"):
                print("[SUCCESS] Agent linked")
                return res.json()["agent_token"]
        except Exception as e:
            print("[WARN] Server not ready:", e)

        time.sleep(3)

# -------------------------
# Command Execution
# -------------------------

def get_system_info():
    try:
        # Uptime in seconds
        uptime = time.time() - psutil.boot_time()
        # Running processes (top 10 by CPU)
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes = sorted(processes, key=lambda x: x['cpu'], reverse=True)[:10]
        return {
            'uptime': uptime,
            'running_apps': processes
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}

def execute_command(command):
    logger.info(f"[COMMAND] Executing: {command}")
    if command == "lock":
        ctypes.windll.user32.LockWorkStation()
        logger.info("[COMMAND] Workstation locked")
    elif command == "shutdown":
        os.system("shutdown /s /t 0")
        logger.info("[COMMAND] Shutdown initiated")
    elif command == "get_info":
        # Server requested info - will be sent in next heartbeat
        logger.info("[COMMAND] Info request acknowledged")
    else:
        logger.warning(f"[COMMAND] Unknown command: {command}")

# -------------------------
#  Heartbeat
# -------------------------

def start_heartbeat(agent_id, agent_token, server_url):
    headers = {"Authorization": f"Bearer {agent_token}"}
    logger.debug("[INFO] Heartbeat started")

    try:
        while True:
            system_info = get_system_info()
            payload = {
                "agent_id": agent_id,
                "system_info": system_info
            }
            try:
                res = requests.post(
                    f"{server_url}/api/agent/heartbeat",
                    json=payload,
                    headers=headers,
                    timeout=5
                )
                if res.status_code == 200:
                    logger.debug("[HEARTBEAT] Sent successfully")
                    data = res.json()
                    commands = data.get("commands", [])
                    for cmd in commands:
                        execute_command(cmd)
                else:
                    logger.warning(f"[HEARTBEAT] Failed with status {res.status_code}")
            except requests.RequestException as e:
                logger.error(f"[HEARTBEAT] Request failed: {e}")
            time.sleep(10)
    except KeyboardInterrupt:
        print("[INFO] Agent stopped")

# -------------------------
# Main
# -------------------------

def main():
    print("[DEBUG] Agent starting...")
    config = load_config()
    print(f"[DEBUG] Config loaded: {config}")

    if "agent_id" not in config:
        config["agent_id"] = generate_agent_id()
        save_config(config)
        print(f"[DEBUG] Generated agent_id: {config['agent_id']}")

    if "agent_token" not in config:
        print("[DEBUG] No token, starting linking...")
        open_browser_for_link(config["agent_id"], config["server_url"])
        config["agent_token"] = wait_for_link(config["agent_id"], config["server_url"])
        save_config(config)
        print(f"[DEBUG] Linked, token: {config['agent_token']}")

    print("[DEBUG] Starting heartbeat...")
    start_heartbeat(config["agent_id"], config["agent_token"], config["server_url"])

if __name__ == "__main__":
    main()

import os
import json
import time
import uuid
import requests
import webbrowser

SERVER_URL = "http://localhost:5000"

APP_DIR = os.path.join(os.getenv("APPDATA"), "ControlIt")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")

# -------------------------
# Utilities
# -------------------------

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    os.makedirs(APP_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# -------------------------
# Agent Registration
# -------------------------

def generate_agent_id():
    return str(uuid.uuid4())

def open_browser_for_link(agent_id):
    url = f"{SERVER_URL}/agent/link?agent_id={agent_id}"
    print("[INFO] Opening browser for linking")
    webbrowser.open(url)

def wait_for_link(agent_id):
    print("[INFO] Waiting for agent to be linked...")
    while True:
        try:
            res = requests.get(
                f"{SERVER_URL}/api/agent/status/{agent_id}",
                timeout=5
            )
            if res.status_code == 200 and res.json().get("linked"):
                print("[SUCCESS] Agent linked")
                return res.json()["agent_token"]
        except Exception as e:
            print("[WARN] Server not ready:", e)

        time.sleep(3)

# -------------------------
# Heartbeat
# -------------------------

def start_heartbeat(agent_id, agent_token):
    headers = {"Authorization": f"Bearer {agent_token}"}
    print("[INFO] Heartbeat started")

    try:
        while True:
            requests.post(
                f"{SERVER_URL}/api/agent/heartbeat",
                json={"agent_id": agent_id},
                headers=headers,
                timeout=5
            )
            time.sleep(10)
    except KeyboardInterrupt:
        print("[INFO] Agent stopped")

# -------------------------
# Main
# -------------------------

def main():
    config = load_config()

    if "agent_id" not in config:
        config["agent_id"] = generate_agent_id()
        save_config(config)

    if "agent_token" not in config:
        open_browser_for_link(config["agent_id"])
        config["agent_token"] = wait_for_link(config["agent_id"])
        save_config(config)

    start_heartbeat(config["agent_id"], config["agent_token"])

if __name__ == "__main__":
    main()

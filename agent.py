import os
import json
import time
import uuid
import requests
import webbrowser
import ctypes
import psutil
import platform
import socket
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
    """Poll the server until agent is linked and gets a token"""
    logger.debug("[INFO] Waiting for agent to be linked...")
    
    # First, register the agent on the server
    try:
        res = requests.post(
            f"{server_url}/api/agent/register",
            json={"agent_id": agent_id},
            timeout=5
        )
        if res.status_code == 200:
            data = res.json()
            if data.get("linked") and data.get("agent_token"):
                logger.debug("[SUCCESS] Agent already linked")
                return data["agent_token"]
            logger.debug("[INFO] Agent registered, waiting for user to link...")
        else:
            logger.warning("[WARN] Failed to register agent: %s", res.status_code)
    except Exception as e:
        logger.debug("[WARN] Registration failed:", e)
    
    # Poll status until linked
    max_attempts = 300  # 30 minutes with 6-second intervals
    attempts = 0
    while attempts < max_attempts:
        try:
            res = requests.get(
                f"{server_url}/api/agent/status/{agent_id}",
                timeout=5
            )
            if res.status_code == 200:
                data = res.json()
                if data.get("linked") and data.get("agent_token"):
                    logger.debug("[SUCCESS] Agent linked")
                    return data["agent_token"]
        except Exception as e:
            logger.debug("[WARN] Status check failed:", e)
        
        attempts += 1
        time.sleep(6)  # Check every 6 seconds
    
    logger.error("[ERROR] Timeout waiting for agent to be linked")
    return None

# -------------------------
# System Information Collection
# -------------------------

def get_os_type():
    """Get OS type: Windows, Linux, or Darwin (macOS)"""
    system = platform.system()
    if system == "Windows":
        return "Windows"
    elif system == "Linux":
        return "Linux"
    elif system == "Darwin":
        return "MacOS"
    else:
        return system

def get_os_version():
    """Get OS version"""
    try:
        if platform.system() == "Windows":
            return f"Windows {platform.release()}"
        else:
            return platform.platform()
    except:
        return "Unknown"

def get_cpu_info():
    """Get CPU model and count"""
    try:
        if platform.system() == "Windows":
            # Use wmi for Windows
            try:
                import wmi
                c = wmi.WMI()
                cpuinfo = c.Win32_Processor()[0]
                return cpuinfo.Name.strip()
            except:
                return platform.processor()
        else:
            return platform.processor()
    except:
        return "Unknown"

def get_total_ram():
    """Get total RAM in GB"""
    try:
        total_bytes = psutil.virtual_memory().total
        total_gb = total_bytes / (1024 ** 3)
        return f"{int(total_gb)}GB"
    except:
        return "Unknown"

def get_ip_address():
    """Get machine IP address"""
    try:
        # Get IP by connecting to a socket (doesn't actually connect)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

def get_cpu_usage():
    """Get CPU usage percentage"""
    try:
        return int(psutil.cpu_percent(interval=1))
    except:
        return 0

def get_ram_usage():
    """Get RAM usage percentage"""
    try:
        return int(psutil.virtual_memory().percent)
    except:
        return 0

def get_system_info():
    """Collect comprehensive system information"""
    try:
        system_info = {
            "type": get_os_type(),
            "osVersion": get_os_version(),
            "cpu": get_cpu_info(),
            "ram": get_total_ram(),
            "cpuUsage": get_cpu_usage(),
            "ramUsage": get_ram_usage(),
            "ipAddress": get_ip_address(),
            "status": "online",
            # Legacy fields for compatibility
            "uptime": time.time() - psutil.boot_time(),
            "timestamp": int(time.time())
        }
        
        # Get running processes (top 5 by CPU)
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
        
        processes = sorted(processes, key=lambda x: x['cpu'], reverse=True)[:5]
        system_info['running_apps'] = processes
        
        return system_info
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {
            "type": get_os_type(),
            "status": "online",
            "cpuUsage": 0,
            "ramUsage": 0
        }

# -------------------------
# Command Execution
# -------------------------

def execute_command(command):
    logger.info(f"[COMMAND] Executing: {command}")
    if command == "lock":
        try:
            if platform.system() == "Windows":
                ctypes.windll.user32.LockWorkStation()
            else:
                os.system("loginctl lock-session")
            logger.info("[COMMAND] Workstation locked")
        except Exception as e:
            logger.error(f"[COMMAND] Failed to lock: {e}")
    elif command == "shutdown":
        try:
            if platform.system() == "Windows":
                os.system("shutdown /s /t 0")
            else:
                os.system("shutdown -h now")
            logger.info("[COMMAND] Shutdown initiated")
        except Exception as e:
            logger.error(f"[COMMAND] Failed to shutdown: {e}")
    elif command == "restart":
        try:
            if platform.system() == "Windows":
                os.system("shutdown /r /t 0")
            else:
                os.system("reboot")
            logger.info("[COMMAND] Restart initiated")
        except Exception as e:
            logger.error(f"[COMMAND] Failed to restart: {e}")
    elif command == "get_info":
        logger.info("[COMMAND] Info request acknowledged")
    else:
        logger.warning(f"[COMMAND] Unknown command: {command}")

# -------------------------
# Heartbeat
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
        logger.debug("[INFO] Agent stopped")

# -------------------------
# Main
# -------------------------

def main():
    logger.debug("[DEBUG] Agent starting...")
    config = load_config()
    logger.debug(f"[DEBUG] Config loaded: {config}")

    if "agent_id" not in config:
        config["agent_id"] = generate_agent_id()
        save_config(config)
        logger.debug(f"[DEBUG] Generated agent_id: {config['agent_id']}")

    if "agent_token" not in config:
        logger.debug("[DEBUG] No token, starting linking...")
        open_browser_for_link(config["agent_id"], config["server_url"])
        config["agent_token"] = wait_for_link(config["agent_id"], config["server_url"])
        save_config(config)
        logger.debug(f"[DEBUG] Linked, token: {config['agent_token']}")

    logger.debug("[DEBUG] Starting heartbeat...")
    start_heartbeat(config["agent_id"], config["agent_token"], config["server_url"])

if __name__ == "__main__":
    main()

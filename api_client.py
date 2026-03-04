import uuid
import requests

SERVER_URL = "http://your-server/api/agent"

def register_agent():
    agent_id = str(uuid.uuid4())

    # later: browser login + token
    return {
        "agent_id": agent_id,
        "agent_token": "dummy-token"
    }

def heartbeat(config):
    print("Heartbeat → server", config["agent_id"])

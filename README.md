# ControlItAppClient

Client-side application for the ControlIt server, enabling remote management of Windows machines. This Python-based agent connects to a ControlIt server for authentication, monitoring, and command execution.

## Features

- **Secure Linking**: Browser-based authentication to link the agent to a user account on the server.
- **Persistent Connection**: Maintains connection via periodic heartbeats to the server.
- **System Monitoring**: Sends uptime and running process information to the server for display.
- **Remote Commands**: Executes commands from the server, such as locking the workstation or initiating shutdown.
- **Configurable**: Easily set server URL and manage local configuration.
- **Logging**: Comprehensive logging with file rotation for debugging and monitoring.

## Requirements

- Python 3.12+
- Windows OS (commands are Windows-specific)
- Dependencies: `requests`, `psutil`, `uuid`

## Installation

1. Clone or download the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Build the executable:
   ```bash
   python build.py
   ```
   The EXE will be in the `dist/` folder.

## Usage

1. Run the `agent.exe` on the client machine.
2. On first run, it will open your browser to the server's login page for linking.
3. Log in/register on the server and link the agent.
4. The agent will start sending heartbeats and await commands.

### Configuration

- Config file: `%APPDATA%\ControlIt\config.json`
- Edit `server_url` to point to your ControlIt server (e.g., `http://198.72.4.5`).
- Other fields (`agent_id`, `agent_token`) are auto-managed.

### Commands Supported

- `lock`: Locks the workstation.
- `shutdown`: Initiates system shutdown.
- `get_info`: Logs info request (system data always sent).

## API Interactions

- **Linking**: `GET {server_url}/login/agent/link?agent_id={id}`
- **Status Check**: `GET {server_url}/api/agent/status/{id}`
- **Heartbeat**: `POST {server_url}/api/agent/heartbeat` (with system info, receives commands)

## Logs

- Location: `%APPDATA%\ControlIt\logs\agent.log`
- Use for troubleshooting connection or command issues.

## Development

- Modify `agent.py` for custom commands or features.
- Rebuild with `python build.py` after changes.
- Test with a local server instance.

## License

[Add license if applicable]

## Contributing

[Add contribution guidelines if applicable]

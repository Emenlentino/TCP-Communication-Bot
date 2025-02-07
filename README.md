# TCP Communication Bot

## Overview
This project is a TCP-based bot designed for secure and efficient communication between hosts. It facilitates message exchange, logs communications, and supports both TCP and MPTCP protocols where available.

## Features
- Supports multiple hosts communication over TCP.
- Logs communications in both CSV and log files.
- Uses `rich` for enhanced console output.
- Supports MPTCP where available.
- Retrieves and logs public and local IP addresses.
- Runs in a multithreaded environment for concurrent message handling.

## Prerequisites
Make sure you have Python 3 installed along with the required dependencies.

### Dependencies
Install the required Python packages using:
```sh
pip install -r requirements.txt
```
Contents of `requirements.txt`:
```
rich
requests
```

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/tcp-communication-bot.git
   cd tcp-communication-bot
   ```
2. Ensure the required directories exist:
   ```sh
   mkdir -p src/logs src/data
   ```
3. Create a `config.json` file specifying hostnames and IP addresses:
   ```json
   {
       "host1": "192.168.1.10",
       "host2": "192.168.1.11",
       "_comment": "Add more hosts as needed"
   }
   ```

## Project Structure:

```
project/
│
├── src/
│   ├── logs/
│   │   └── communication.log
│   ├── data/
│   │   └── communication.csv
│   └── ip_bot.py
│
├── config.json
└── requirements.txt
```

## Usage
Run the bot using:
```sh
python tcp_app.py <hostname> <mptcp_enabled>
```
Example:
```sh
python tcp_app.py host1 true
```

### Logging
Logs are saved in:
- `src/logs/communication.log` (for errors and events)
- `src/data/communication.csv` (for structured communication logs)

## Troubleshooting
- Ensure `config.json` exists and contains valid host entries.
- If MPTCP is not supported, the bot will default to TCP.
- Check log files for any connection issues.

## License
This project is licensed under the MIT License.

## Contributing
Feel free to submit issues and pull requests to improve this project.


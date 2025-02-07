import sys
import socket
import json
import threading
import time
import logging
import requests
import csv
import os
from rich.console import Console
from rich.logging import RichHandler
from datetime import datetime

# Initialize the rich console
console = Console()

# Create necessary directories
os.makedirs('src/logs', exist_ok=True)
os.makedirs('src/data', exist_ok=True)

# Configure logging to use RichHandler and file logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        RichHandler(),
        logging.FileHandler('src/logs/communication.log')
    ]
)
logger = logging.getLogger("rich")

HOST_PORT_START = 5000  # Starting port number for hosts
SOCKET_PROTO = socket.IPPROTO_TCP  # Default protocol

# Check if IPPROTO_MPTCP is available and set it if it is
try:
    SOCKET_PROTO = socket.IPPROTO_MPTCP
except AttributeError:
    logger.warning("IPPROTO_MPTCP is not available. Using IPPROTO_TCP instead.")
    SOCKET_PROTO = socket.IPPROTO_TCP

def log_to_csv(action, hostname, other_hostname, ip, port, status):
    file_exists = os.path.isfile('src/data/communication.csv')
    with open('src/data/communication.csv', 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'action', 'hostname', 'other_hostname', 'ip', 'port', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': action,
            'hostname': hostname,
            'other_hostname': other_hostname,
            'ip': ip,
            'port': port,
            'status': status
        })

def communicate_with_other_hosts(hostname, ip_address, port, config_data):
    """This function will handle both listening and communicating with other hosts."""
    # Use 0.0.0.0 to bind to all available network interfaces
    bind_address = "0.0.0.0"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, SOCKET_PROTO)
    server_socket.bind((bind_address, port))
    server_socket.listen(len(config_data))  # Number of hosts in the network
    console.print(f"[bold green]Host {hostname} listening on {bind_address}:{port}.[/bold green]")

    # Function to accept connections and receive messages
    def accept_connections():
        while True:
            try:
                conn, addr = server_socket.accept()
                data = conn.recv(1024).decode()
                console.print(f"[bold cyan]{hostname} received from {addr}: {data}[/bold cyan]")
                logger.info(f"{hostname} received from {addr}: {data}")
                log_to_csv('receive', hostname, addr[0], addr[0], addr[1], 'success')
                conn.close()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
                log_to_csv('receive', hostname, 'N/A', 'N/A', 'N/A', 'error')

    # Start a thread to handle incoming connections
    threading.Thread(target=accept_connections, daemon=True).start()

    # Periodically send messages to all other hosts
    def send_messages():
        while True:
            for other_hostname, other_ip in config_data.items():
                if other_hostname == "_comment" or other_hostname == hostname:  # Skip comments and self
                    continue
                other_port = HOST_PORT_START + list(config_data.keys()).index(other_hostname)
                logger.info(f"Attempting to connect to {other_hostname} at {other_ip}:{other_port}")
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, SOCKET_PROTO)
                    client_socket.settimeout(5)  # Set a timeout for connection attempts
                    client_socket.connect((other_ip, other_port))
                    message = f"Hello from {hostname} to {other_hostname}"
                    client_socket.send(message.encode())
                    client_socket.close()
                    logger.info(f"Sent message from {hostname} to {other_hostname} at {other_ip}:{other_port}")
                    log_to_csv('send', hostname, other_hostname, other_ip, other_port, 'success')
                except socket.gaierror as e:
                    logger.error(f"Address-related error connecting to {other_hostname} at {other_ip}:{other_port} - {e}")
                    log_to_csv('send', hostname, other_hostname, other_ip, other_port, 'address error')
                except ConnectionRefusedError as e:
                    logger.error(f"Connection refused connecting to {other_hostname} at {other_ip}:{other_port} - {e}")
                    log_to_csv('send', hostname, other_hostname, other_ip, other_port, 'refused')
                except TimeoutError as e:
                    logger.error(f"Connection to {other_hostname} at {other_ip}:{other_port} timed out - {e}")
                    log_to_csv('send', hostname, other_hostname, other_ip, other_port, 'timeout')
                except Exception as e:
                    logger.error(f"Unexpected error connecting to {other_hostname} at {other_ip}:{other_port} - {e}")
                    log_to_csv('send', hostname, other_hostname, other_ip, other_port, 'error')
            time.sleep(5)  # Adjust the sleep time as needed

    # Start a thread to send messages periodically
    threading.Thread(target=send_messages, daemon=True).start()

    try:
        while True:
            time.sleep(1)  # Sleep to prevent the loop from consuming excessive CPU
    except KeyboardInterrupt:
        console.print(f"[bold red]{hostname} interrupted, stopping.[/bold red]")
        server_socket.close()

def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        return response.json()["ip"]
    except requests.RequestException as e:
        logger.error(f"Error fetching public IP: {e}")
        return None

def get_local_ip():
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except socket.error as e:
        logger.error(f"Error fetching local IP: {e}")
        return None

def main():
    if len(sys.argv) != 3:
        console.print("[bold red]Usage: python tcp_app.py <hostname> <mptcp_enabled>[/bold red]")
        sys.exit(1)

    hostname = sys.argv[1]

    if sys.argv[2] == "true":
        try:
            console.print("[bold green]Enabled MPTCP[/bold green]")
            global SOCKET_PROTO
            SOCKET_PROTO = socket.IPPROTO_MPTCP
        except AttributeError:
            console.print("[bold red]IPPROTO_MPTCP is not supported on this system. Using IPPROTO_TCP instead.[/bold red]")

    console.print(f"Socket Protocol: [bold cyan]{SOCKET_PROTO}[/bold cyan]")

    # Load the configuration from the JSON file
    config_file_path = 'config.json'
    try:
        with open(config_file_path, 'r') as config_file:
            console.print(f"[bold green]Loading configuration from {config_file_path}...[/bold green]")
            config_data = json.load(config_file)
            console.print(f"[bold green]Configuration loaded successfully.[/bold green]")
            logger.info(f"Config Data: {config_data}")
    except FileNotFoundError:
        console.print(f"[bold red]Configuration file {config_file_path} not found.[/bold red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error decoding JSON from {config_file_path}: {e}[/bold red]")
        sys.exit(1)

    ip_address = config_data.get(hostname)
    if not ip_address:
        console.print(f"[bold red]Hostname {hostname} not found in config.[/bold red]")
        sys.exit(1)

    port = HOST_PORT_START + list(config_data.keys()).index(hostname)

    public_ip = get_public_ip()
    if public_ip:
        logger.info(f"Your public IP address is: [bold cyan]{public_ip}[/bold cyan]")

    local_ip = get_local_ip()
    if local_ip:
        logger.info(f"Your local IP address is: [bold cyan]{local_ip}[/bold cyan]")

    communicate_with_other_hosts(hostname, ip_address, port, config_data)

if __name__ == "__main__":
    main()

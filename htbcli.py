import os
import time
import requests
import argparse
import sys
import json
from prettytable import PrettyTable

BASE = "https://labs.hackthebox.com"
#BASE = "http://127.0.0.1:4444"
API_URL_MACHINES = f"{BASE}/api/v4/season/machines"
API_URL_START_VM = f"{BASE}/api/v4/vm/spawn"
API_URL_STOP_VM = f"{BASE}/api/v4/vm/terminate"
API_URL_ACTIVE_MACHINE = f"{BASE}/api/v4/machine/profile"
API_URL_LIST_MACHINES = f"{BASE}/api/v4/season/machines"
API_URL_INFO_MACHINE = f"{BASE}/api/v4/machine/profile"
#API_URL_SUBMIT_FLAG = f"{BASE}/api/v5/machine/own"
API_URL_SUBMIT_FLAG = f"{BASE}/api/v4/arena/own"

DEFAULT_TIMEOUT = 10  # seconds for HTTP requests
POLL_INTERVAL = 10    # seconds between active checks

def fetch_machines(token):
    """Fetch the list of seasons from the HackTheBox API."""
    htb_headers = {"Authorization": f"Bearer {token}","User-Agent": "xxx/1.0","Accept": "application/json",}
    response = requests.get(API_URL_LIST_MACHINES, headers=htb_headers)
    response.raise_for_status()  # Raises an error if the request fails
    print_season_table(response.json())
    return response.json()

def print_season_table(data):
    """Print a formatted table of season info."""
    table_data = [(item["id"], item["name"], item["os"]) for item in data["data"] if not item.get("unknown")]

    #print(tabulate(table_data, headers=["name", "id", "os"], tablefmt="grid"))

    print(f"{'Name':<20} {'id':<6} {'os':<20}")
    print("-" * 46)

    # Print rows
    for id, name, os in table_data:
        print(f"{name:<20} {id:<6} {os:<20}")

def get_machine_id_by_name(api_url, machine_name, token, timeout=DEFAULT_TIMEOUT):
    """Fetch machines and return the ID for the given machine_name (case-insensitive)."""
    htb_headers = {"Authorization": f"Bearer {token}","User-Agent": "xxx/1.0","Accept": "application/json",}
    try:
        resp = requests.get(api_url, headers=htb_headers)
        resp.raise_for_status()
        data = resp.json()
        machines = data.get("data", [])
        for machine in machines:
            if machine.get("name", "").lower() == machine_name.lower():
                return machine.get("id")
        print(f"Machine '{machine_name}' not found.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[get_machine_id_by_name] Request error: {e}")
        return None
    except ValueError:
        print("[get_machine_id_by_name] Failed to parse JSON.")
        return None


def start_machine(api_url, machine_id, token, timeout=DEFAULT_TIMEOUT):
    """Start a VM by POSTing JSON { "machine_id": <id> }."""
    htb_headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "xxx/1.0",
        "Content-Type": "application/json",
    }
    payload = {"machine_id": machine_id}
    try:
        resp = requests.post(api_url, headers=htb_headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        print(f"Machine {machine_id} start request sent successfully.")
        # return the JSON response for inspection if needed
        try:
            return resp.json()
        except ValueError:
            return {}
    except requests.exceptions.HTTPError as http_err:
        text = getattr(resp, "text", "")
        print(f"[start_machine] HTTP error: {http_err} - {text}")
    except requests.exceptions.RequestException as e:
        print(f"[start_machine] Request error: {e}")
    return None

def stop_machine(api_url, machine_id, token, timeout=DEFAULT_TIMEOUT):
    """Stop a VM by POSTing JSON { "machine_id": <id> }."""
    htb_headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "xxx/1.0",
        "Content-Type": "application/json",
    }
    payload = {"machine_id": machine_id}
    try:
        resp = requests.post(api_url, headers=htb_headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        print(f"Machine {machine_id} stop request sent successfully.")
        # return the JSON response for inspection if needed
        try:
            return resp.json()
        except ValueError:
            return {}
    except requests.exceptions.HTTPError as http_err:
        text = getattr(resp, "text", "")
        print(f"[stop_machine] HTTP error: {http_err} - {text}")
    except requests.exceptions.RequestException as e:
        print(f"[stop_machine] Request error: {e}")
    return None

def wait_for_machine_ip(api_url, token, machine_id, poll_interval=POLL_INTERVAL, timeout=DEFAULT_TIMEOUT):
    """
    Polls the active machine endpoint until isSpawning is False.
    Returns the IP address string when ready, or None on error.
    """
    htb_headers = {"Authorization": f"Bearer {token}","User-Agent": "xxx/1.0","Accept": "application/json",}
    print("Waiting for machine to finish spawning...")
    while True:
        try:
            resp = requests.get(api_url + '/' + f"{machine_id}", headers=htb_headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            info = data.get("info", {})
            if not info:
                print("No 'info' returned from active endpoint. Retrying...")
            else:
                machine_ip = data['info']['ip']
                name = data.get('info', {}).get('name')
                mid = machine_id
                if machine_ip is not None :
                    print(f"Machine is ready! (id={mid}, name={name}, ip={machine_ip})")
                    return machine_ip
                else:
                    print(f"Machine (id={mid}, name={name}) is still spawning... waiting {poll_interval}s.")
        except requests.exceptions.RequestException as e:
            print(f"[wait_for_machine_ip] Request error: {e}")

        time.sleep(poll_interval)

def start_command(machine_name, TOKEN):

    machine_id = get_machine_id_by_name(API_URL_MACHINES, machine_name, TOKEN)
    if machine_id is None:
        exit(1)

    print(f"Found machine '{machine_name}' with ID {machine_id}.")
    confirm = input(f"Do you want to start '{machine_name}'? (y/n): ").strip().lower()
    if confirm != "y":
        print("Operation cancelled.")
        exit(0)

    start_resp = start_machine(API_URL_START_VM, machine_id, TOKEN)
    if start_resp is None:
        print("Failed to start machine.")
        exit(1)

    ip = wait_for_machine_ip(API_URL_ACTIVE_MACHINE, TOKEN, machine_id)
    if ip:
        print(f"Final machine IP: {ip}")
    else:
        print("Failed to obtain machine IP.")

def stop_command(machine_name, TOKEN):
    machine_id = get_machine_id_by_name(API_URL_MACHINES, machine_name, TOKEN)
    if machine_id is None:
        exit(1)

    stop_resp = stop_machine(API_URL_STOP_VM, machine_id, TOKEN)
    if stop_resp is None:
        print("Failed to start machine.")
        exit(1)

    return

def flag_command(flag, token):
    htb_headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "xxx/1.0",
        "Content-Type": "application/json",
    }
    payload = {"flag": flag}
    try:
        resp = requests.post(API_URL_SUBMIT_FLAG, headers=htb_headers, json=payload)
        resp.raise_for_status()
        print(f"Flag {flag} submitted successfully")
        # return the JSON response for inspection if needed
        try:
            return resp.json()
        except ValueError:
            return {}
    except requests.exceptions.HTTPError as http_err:
        text = getattr(resp, "text", "")
        print(f"[submit_flag] HTTP error: {http_err} - {text}")
    except requests.exceptions.RequestException as e:
        print(f"[submit_flag] Request error: {e}")
    return None

def info_command(machine, token):
    """Fetch the list of seasons from the HackTheBox API."""
    htb_headers = {"Authorization": f"Bearer {token}","User-Agent": "xxx/1.0","Accept": "application/json",}
    response = requests.get(API_URL_INFO_MACHINE + '/' + machine, headers=htb_headers)
    response.raise_for_status()  # Raises an error if the request fails
    data = response.json()
    info_status = data.get("info", {}).get("info_status")
    print("Description:", info_status)
    return None

if __name__ == "__main__":
    # get token
    TOKEN = os.getenv("HTB_API_TOKEN")
    if not TOKEN:
        print("Error: HTB_API_TOKEN environment variable not set.")
        exit(1)

    parser = argparse.ArgumentParser(
        description="Process machine control commands."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list command
    subparsers.add_parser("list", help="List all machines")

    # start command
    parser_start = subparsers.add_parser("start", help="Start a machine")
    parser_start.add_argument("--machine", required=True, help="Machine name")

    # stop command
    parser_stop = subparsers.add_parser("stop", help="Stop a machine")
    parser_stop.add_argument("--machine", required=True, help="Machine name")

    # flag command
    parser_flag = subparsers.add_parser("flag", help="Submit a flag")
    parser_flag.add_argument("--submit_flag", required=True, help="Flag value to submit")

    # info command
    parser_start = subparsers.add_parser("info", help="info about a machine")
    parser_start.add_argument("--machine", required=True, help="Machine name")

    args = parser.parse_args()

    # Command dispatcher
    if args.command == "list":
        fetch_machines(TOKEN)
    elif args.command == "start":
        start_command(args.machine, TOKEN)
    elif args.command == "stop":
        stop_command(args.machine, TOKEN)
    elif args.command == "flag":
        flag_command(args.submit_flag, TOKEN)
    elif args.command == "info":
        info_command(args.machine, TOKEN)
    else:
        parser.print_help()
        sys.exit(1)

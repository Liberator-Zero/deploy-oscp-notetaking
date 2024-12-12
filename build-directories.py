import os
import re
import argparse
from termcolor import colored
import subprocess
import logging
from datetime import datetime
import psutil

# Setup logging
logging.basicConfig(filename='deployment.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Directory to store backups
BACKUP_DIR = "/etc/hosts_backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# Function to validate IP address
def is_valid_ip(ip):
    ip_pattern = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')
    return bool(ip_pattern.match(ip)) and all(0 <= int(octet) <= 255 for octet in ip.split('.'))

# Function to validate system name (alphanumeric, periods, and capital letters allowed)
def is_valid_name(name):
    pattern = re.compile(r'^[a-zA-Z0-9\.]+$')
    return bool(pattern.match(name))

# Create backup of /etc/hosts with timestamp and update it with new entries
def update_etc_hosts(hostname, ip, target_type="oscp.exam", remove=False):
    try:
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = f"{BACKUP_DIR}/hosts.bak.{timestamp}"
        os.system(f"cp /etc/hosts {backup_file}")
        logging.info(f"Backup created: {backup_file}")

        # Keep only the latest 5 backups
        backups = sorted(os.listdir(BACKUP_DIR), reverse=True)
        for backup in backups[5:]:
            os.remove(os.path.join(BACKUP_DIR, backup))
            logging.info(f"Old backup {backup} removed.")

        with open('/etc/hosts', 'r') as hosts_file:
            lines = hosts_file.readlines()

        # Handle removing or adding entries
        updated_lines = []
        for line in lines:
            if remove and (f"{hostname}.{target_type}" in line):
                continue  # Skip the lines we want to remove
            elif not remove and (ip in line or f"{hostname}.{target_type}" in line):
                continue  # Remove existing entries for hostname/ip

            updated_lines.append(line)
        
        # Add the new entry (if not removing)
        if not remove:
            updated_lines.append(f"{ip} {hostname}.{target_type}\n")

        # Write back to /etc/hosts
        with open('/etc/hosts', 'w') as hosts_file:
            hosts_file.writelines(updated_lines)

        action = "Added" if not remove else "Removed"
        print(colored(f"{action} {hostname}.{target_type} to /etc/hosts", "yellow"))
        logging.info(f"{action} {hostname}.{target_type} to /etc/hosts")
    except PermissionError:
        print(colored("Permission denied: Unable to modify /etc/hosts. Please run the script with elevated privileges.", "red"))
        logging.error("Permission denied while modifying /etc/hosts.")
    except Exception as e:
        print(colored(f"An error occurred while modifying /etc/hosts: {e}", "red"))
        logging.error(f"Error modifying /etc/hosts: {e}")

# Remove all entries from /etc/hosts for .pg and .oscp.exam
def remove_from_etc_hosts(target_type="both"):
    try:
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = f"{BACKUP_DIR}/hosts.bak.{timestamp}"
        os.system(f"cp /etc/hosts {backup_file}")
        logging.info(f"Backup created: {backup_file}")

        # Keep only the latest 5 backups
        backups = sorted(os.listdir(BACKUP_DIR), reverse=True)
        for backup in backups[5:]:
            os.remove(os.path.join(BACKUP_DIR, backup))
            logging.info(f"Old backup {backup} removed.")

        with open('/etc/hosts', 'r') as hosts_file:
            lines = hosts_file.readlines()

        # Remove all entries with .pg or .oscp.exam
        updated_lines = []
        for line in lines:
            if target_type == "both" and (".pg" in line or ".oscp.exam" in line):
                continue
            if target_type == "pg" and ".pg" in line:
                continue
            if target_type == "oscp.exam" and ".oscp.exam" in line:
                continue
            updated_lines.append(line)

        with open('/etc/hosts', 'w') as hosts_file:
            hosts_file.writelines(updated_lines)

        print(colored(f"Removed {target_type} entries from /etc/hosts", "yellow"))
        logging.info(f"Removed {target_type} entries from /etc/hosts")
    except PermissionError:
        print(colored("Permission denied: Unable to modify /etc/hosts. Please run the script with elevated privileges.", "red"))
        logging.error("Permission denied while modifying /etc/hosts.")
    except Exception as e:
        print(colored(f"An error occurred while removing from /etc/hosts: {e}", "red"))
        logging.error(f"Error removing from /etc/hosts: {e}")

# Start a web server in the background
def start_web_server_in_background(directory, port):
    try:
        command = f"python3 -m http.server {port} --directory {directory} &"
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(colored(f"Web server started in background serving {directory} on port {port}", "green"))
        logging.info(f"Web server started on port {port} serving directory {directory}")
    except Exception as e:
        print(colored(f"Failed to start web server: {e}", "red"))
        logging.error(f"Failed to start web server on port {port}: {e}")

# Stop all web servers by terminating background processes using psutil
def stop_web_servers():
    try:
        # Iterate over all processes and find those running the web server
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            # Check if the process is running the HTTP server
            if 'python3' in proc.info['name'] and 'http.server' in ' '.join(proc.info['cmdline']):
                # Kill the process
                proc.kill()
                print(colored(f"Stopped web server with PID {proc.info['pid']}.", "yellow"))
                logging.info(f"Stopped web server with PID {proc.info['pid']}.")
    except psutil.NoSuchProcess:
        print(colored("No web servers are running.", "yellow"))
        logging.info("No web servers are running.")
    except Exception as e:
        print(colored(f"An error occurred while stopping web servers: {e}", "red"))
        logging.error(f"Error stopping web servers: {e}")

# Function to create the directory structure for multiple targets (OSCP)
def create_directory_structure(base_folder, target_type="oscp.exam"):
    directory_structure = {
        "standalone": [],
        "active_directory": [],
        "payloads": []
    }

    ips = {}
    try:
        # Loop to gather system names and IPs
        num_standalone = 3
        for i in range(1, num_standalone + 1):
            system_name = input(f"Enter name for Host {i}: ").strip()
            while not is_valid_name(system_name):
                print("Invalid name. Only alphanumeric characters and periods are allowed.")
                system_name = input(f"Enter name for Host {i}: ").strip()

            ip_address = input(f"Enter IP address for {system_name}: ").strip()
            while not is_valid_ip(ip_address):
                print("Invalid IP address. Please enter again.")
                ip_address = input(f"Enter IP address for {system_name}: ").strip()

            directory_structure["standalone"].append(f"{system_name}_{ip_address}")
            ips[system_name] = ip_address
            update_etc_hosts(system_name, ip_address, target_type)

        # Loop to gather Active Directory machine IPs (including hostnames)
        ad_machines = ["external_device", "internal_device", "domain_controller"]
        for machine in ad_machines:
            hostname = input(f"Enter hostname for {machine}: ").strip()
            while not is_valid_name(hostname):
                print("Invalid hostname. Only alphanumeric characters and periods are allowed.")
                hostname = input(f"Enter hostname for {machine}: ").strip()

            ip_address = input(f"Enter IP address for {hostname}: ").strip()
            while not is_valid_ip(ip_address):
                print("Invalid IP address. Please enter again.")
                ip_address = input(f"Enter IP address for {hostname}: ").strip()

            directory_structure["active_directory"].append(f"{hostname}_{ip_address}")
            ips[hostname] = ip_address
            update_etc_hosts(hostname, ip_address, target_type)

        # Create the directories for all systems
        os.makedirs(base_folder, exist_ok=True)
        os.makedirs(os.path.join(base_folder, "payloads", "tools-ingress"), exist_ok=True)
        start_web_server_in_background(os.path.join(base_folder, "payloads", "tools-ingress"), 8443)

        for main_folder, subfolders in directory_structure.items():
            main_path = os.path.join(base_folder, main_folder)
            os.makedirs(main_path, exist_ok=True)
            for subfolder in subfolders:
                system_path = os.path.join(main_path, subfolder)
                os.makedirs(system_path, exist_ok=True)
                for subfolder_name in ["notes", "scans", "exploits", "proofs", "screenshots", "hashes"]:
                    os.makedirs(os.path.join(system_path, subfolder_name), exist_ok=True)

        print(colored(f"Directory structure created successfully under: {base_folder}", "green"))
        logging.info(f"Directory structure created under: {base_folder}")
    except Exception as e:
        print(colored(f"An error occurred while creating the directory structure: {e}", "red"))
        logging.error(f"Error creating directory structure: {e}")
    return ips

# Function to create directory structure for a single target (PG)
def create_single_target_directory(base_folder, target_name):
    try:
        pg_folder = os.path.join(base_folder, target_name)
        if os.path.exists(pg_folder):
            print(colored(f"Directory {pg_folder} already exists. Skipping creation.", "yellow"))
            return

        ip_address = input(f"Enter IP address for {target_name}: ").strip()
        while not is_valid_ip(ip_address):
            print("Invalid IP address. Please enter again.")
            ip_address = input(f"Enter IP address for {target_name}: ").strip()

        os.makedirs(pg_folder, exist_ok=True)
        update_etc_hosts(target_name, ip_address, "pg")

        subfolders = ["notes", "scans", "exploits", "proofs", "screenshots", "hashes"]
        for subfolder in subfolders:
            os.makedirs(os.path.join(pg_folder, subfolder), exist_ok=True)

        os.makedirs(os.path.join(pg_folder, "payloads", "tools-ingress"), exist_ok=True)
        start_web_server_in_background(os.path.join(pg_folder, "payloads", "tools-ingress"), 8444)

        print(colored(f"Single target directory created for {target_name} under: {pg_folder}", "green"))
        logging.info(f"Single target directory created for {target_name} under: {pg_folder}")
    except Exception as e:
        print(colored(f"An error occurred while creating the single target directory: {e}", "red"))
        logging.error(f"Error creating single target directory: {e}")

# Main execution based on arguments
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy OSCP structure or create single target directory")
    parser.add_argument("--deploy-oscp", action="store_true", help="Deploy the full OSCP directory structure")
    parser.add_argument("--deploy-pg", type=str, help="Create directory structure for a single PG target system")
    parser.add_argument("--cleanup", action="store_true", help="Clean up .pg and .oscp.exam entries and stop web servers")
    
    args = parser.parse_args()

    if args.deploy_oscp:
        base_folder = "oscp-exam"
        create_directory_structure(base_folder, "oscp.exam")
    elif args.deploy_pg:
        target_name = args.deploy_pg
        base_folder = "PG"
        create_single_target_directory(base_folder, target_name)
    elif args.cleanup:
        remove_from_etc_hosts("both")
        stop_web_servers()
    else:
        print("Please specify either --deploy-oscp, --deploy-pg <name>, or --cleanup")

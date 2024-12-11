import os
import re
from termcolor import colored
import subprocess

def is_valid_ip(ip):
    ip_pattern = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')
    if ip_pattern.match(ip):
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)
    return False

def is_valid_name(name):
    return name.isalpha() and name.islower()

def add_to_etc_hosts(hostname, ip):
    try:
        # Create a backup of /etc/hosts
        os.system("cp /etc/hosts /etc/hosts.bak")
        with open('/etc/hosts', 'r') as hosts_file:
            lines = hosts_file.readlines()

        # Remove existing entries for the IP or hostname
        updated_lines = [line for line in lines if not (ip in line or f"{hostname}.oscp" in line)]
        updated_lines.append(f"{ip} {hostname}.oscp\n")

        with open('/etc/hosts', 'w') as hosts_file:
            hosts_file.writelines(updated_lines)

        print(colored(f"Added {hostname}.oscp to /etc/hosts", "yellow"))
    except PermissionError:
        print(colored("Permission denied: Unable to modify /etc/hosts. Please run the script with elevated privileges.", "red"))
    except Exception as e:
        print(colored(f"An error occurred while modifying /etc/hosts: {e}", "red"))

def start_web_server_in_background(directory, port):
    try:
        command = f"python3 -m http.server {port} --directory {directory} &"
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(colored(f"Web server started in background serving {directory} on port {port}", "green"))
    except Exception as e:
        print(colored(f"Failed to start web server: {e}", "red"))

def create_oscp_directory_structure(base_folder, automated_inputs=None):
    directory_structure = {
        "standalone": [],
        "active_directory": [],
        "payloads": []
    }

    standalone_ips = {}
    active_directory_ips = {}

    if automated_inputs:
        # Use predefined inputs for automation
        for system_name, ip_address in automated_inputs.get("standalone", {}).items():
            directory_structure["standalone"].append(f"{system_name}_{ip_address}")
            standalone_ips[system_name] = ip_address

        for machine, ip_address in automated_inputs.get("active_directory", {}).items():
            directory_structure["active_directory"].append(f"{machine}_{ip_address}")
            active_directory_ips[machine] = ip_address
    else:
        # Prompt user for standalone system names and IPs
        num_standalone = 3
        print(f"Please enter names and IP addresses for {num_standalone} standalone systems:")
        for i in range(1, num_standalone + 1):
            system_name = input(f"Enter name for standalone system {i} (lowercase alphabetic only): ").strip()
            while not is_valid_name(system_name):
                print("Invalid name. Only lowercase alphabetical characters are allowed.")
                system_name = input(f"Enter name for standalone system {i} (lowercase alphabetic only): ").strip()

            ip_address = input(f"Enter IP address for {system_name}: ").strip()
            while not is_valid_ip(ip_address):
                print("Invalid IP address. Please enter again.")
                ip_address = input(f"Enter IP address for {system_name}: ").strip()

            directory_structure["standalone"].append(f"{system_name}_{ip_address}")
            standalone_ips[system_name] = ip_address
            add_to_etc_hosts(system_name, ip_address)

        # Prompt user for Active Directory machine IPs
        ad_machines = ["external_device", "internal_device", "domain_controller"]
        print(f"Please enter IP addresses for the following Active Directory machines:")
        for machine in ad_machines:
            ip_address = input(f"Enter IP address for {machine}: ").strip()
            while not is_valid_ip(ip_address):
                print("Invalid IP address. Please enter again.")
                ip_address = input(f"Enter IP address for {machine}: ").strip()
            directory_structure["active_directory"].append(f"{machine}_{ip_address}")
            active_directory_ips[machine] = ip_address

    # Create base folder and subfolders
    try:
        os.makedirs(base_folder, exist_ok=True)
        os.makedirs(os.path.join(base_folder, "github-clones"), exist_ok=True)
        tools_ingress_path = os.path.join(base_folder, "payloads", "tools-ingress")
        os.makedirs(tools_ingress_path, exist_ok=True)

        # Start a web server in the tools-ingress folder
        start_web_server_in_background(tools_ingress_path, 8443)

        for main_folder, subfolders in directory_structure.items():
            main_path = os.path.join(base_folder, main_folder)
            os.makedirs(main_path, exist_ok=True)
            for subfolder in subfolders:
                system_path = os.path.join(main_path, subfolder)
                os.makedirs(system_path, exist_ok=True)
                for subfolder_name in ["notes", "scans", "exploits", "proofs", "screenshots", "hashes"]:
                    os.makedirs(os.path.join(system_path, subfolder_name), exist_ok=True)
                    # Copy rockyou.txt to the hashes folder
                    if subfolder_name == "hashes":
                        rockyou_source = "/usr/share/wordlists/rockyou.txt"
                        rockyou_dest = os.path.join(system_path, subfolder_name, "rockyou.txt")
                        if os.path.exists(rockyou_source):
                            try:
                                os.system(f"cp {rockyou_source} {rockyou_dest}")
                                print(colored(f"Copied rockyou.txt to {os.path.join(system_path, subfolder_name)}", "yellow"))
                            except Exception as e:
                                print(colored(f"Failed to copy rockyou.txt: {e}", "red"))
                # Create an empty CherryTree file in the notes folder
                cherrytree_file = os.path.join(system_path, "notes", f"{subfolder}.ctb")
                with open(cherrytree_file, "w") as ct_file:
                    pass

        print(colored(f"Directory structure created successfully under: {base_folder}", "green"))

        # Change ownership to avoid permission issues
        try:
            os.system(f"chown -R christopher:christopher {base_folder}")
            print(colored(f"Ownership of {base_folder} changed to christopher:christopher", "yellow"))
        except Exception as e:
            print(colored(f"Failed to change ownership: {e}", "red"))

        # Log structure to file
        log_file = os.path.join(base_folder, "structure_log.txt")
        with open(log_file, "w") as log:
            log.write("Standalone Systems:\n")
            for name, ip in standalone_ips.items():
                log.write(f"{name}: {ip}\n")
            log.write("\nActive Directory Machines:\n")
            for name, ip in active_directory_ips.items():
                log.write(f"{name}: {ip}\n")

        print(colored(f"Log file created at: {log_file}", "blue"))

    except Exception as e:
        print(colored(f"An error occurred while creating the directory structure: {e}", "red"))

    return standalone_ips, active_directory_ips

# Usage example
if __name__ == "__main__":
    if os.geteuid() != 0:
        print(colored("This script must be run as root to modify /etc/hosts and set ownership.", "red"))
        exit(1)

    base_folder = "oscp-exam"
    standalone_ips, active_directory_ips = create_oscp_directory_structure(base_folder)
    print("Standalone IPs:", standalone_ips)
    print("Active Directory IPs:", active_directory_ips)

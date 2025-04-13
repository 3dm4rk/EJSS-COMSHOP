#with shutdown and volume control features

import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor

# Configuration
PORT = 12345  # Port to scan and send messages to
TIMEOUT = 1  # Timeout for port scanning (in seconds)

# List of units and their IP addresses
UNITS = {
    "1": "192.168.1.19",
    "2": "192.168.1.4",
    "3": "192.168.1.11",
    "4": "192.168.1.3"
}

def is_port_open(ip, port):
    """
    Check if a port is open on a given IP address.
    Returns True if the port is open, otherwise False.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(TIMEOUT)
            result = sock.connect_ex((ip, port))
            return result == 0  # Port is open if result is 0
    except Exception:
        return False

def scan_network(network_range):
    """
    Scan a network range for devices with the receiver port open.
    Returns a list of IP addresses with open ports.
    """
    open_ips = []
    print(f"Scanning network {network_range} for open ports...")

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {
            executor.submit(is_port_open, str(ip), PORT): ip
            for ip in ipaddress.IPv4Network(network_range)
        }
        for future in futures:
            ip = futures[future]
            if future.result():
                print(f"Found open port at {ip}:{PORT}")
                open_ips.append(str(ip))

    return open_ips

def send_message(message, target_ip):
    """
    Send a message to the receiver at the specified IP address.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(TIMEOUT)
            client_socket.connect((target_ip, PORT))
            client_socket.sendall(message.encode("utf-8"))
            print(f"Message sent to {target_ip}:{PORT}")
    except socket.timeout:
        print(f"Connection to {target_ip}:{PORT} timed out.")
    except ConnectionRefusedError:
        print(f"Connection to {target_ip}:{PORT} refused.")
    except Exception as e:
        print(f"Failed to send message to {target_ip}:{PORT}. Error: {e}")

def send_to_all_units(message):
    """
    Send a message to all units in the UNITS dictionary.
    """
    for unit, ip in UNITS.items():
        print(f"Sending to Unit {unit} ({ip})...")
        send_message(message, ip)

def auto_send(message, network_range):
    """
    Automatically scan the network and send messages to devices with open ports.
    """
    open_ips = scan_network(network_range)
    if not open_ips:
        print("No open ports found.")
        return

    print(f"Sending message to {len(open_ips)} devices...")
    for ip in open_ips:
        send_message(message, ip)

def check_device_status():
    """
    Check the status of all devices in the UNITS dictionary.
    Prints whether each device is active (port open) or inactive (port closed).
    """
    print("\nChecking device status...")
    for unit, ip in UNITS.items():
        status = "Active" if is_port_open(ip, PORT) else "Inactive"
        print(f"Unit {unit} ({ip}): {status}")

def shutdown_unit(unit_ip):
    """
    Send a shutdown command to the specified unit IP address.
    """
    send_message("SHUTDOWN", unit_ip)

def set_unit_volume(unit_ip, volume_percent):
    """
    Send a volume adjustment command to the specified unit IP address.
    The command will be in the format: VOLUME:50 (for 50%)
    """
    send_message(f"VOLUME:{volume_percent}", unit_ip)

def custom_ip_submenu(custom_ip):
    """
    Display a sub-menu for a custom IP with options to send a message, shutdown, adjust volume, or go back.
    """
    while True:
        print("\n--- Custom IP Options ---")
        print(f"IP Address: {custom_ip}")
        print("[1] Send Message")
        print("[2] Shutdown")
        print("[3] Adjust Speaker Volume")
        print("[4] Back to Main Menu")
        sub_choice = input("Enter your choice (1-4): ")

        if sub_choice == "1":
            message = input("Enter the message to send: ")
            send_message(message, custom_ip)
        elif sub_choice == "2":
            shutdown_unit(custom_ip)
        elif sub_choice == "3":
            try:
                volume = int(input("Enter volume percentage (0-100): "))
                if 0 <= volume <= 100:
                    set_unit_volume(custom_ip, volume)
                    print(f"Volume set to {volume}% sent to {custom_ip}")
                else:
                    print("Please enter a value between 0 and 100")
            except ValueError:
                print("Please enter a valid number")
        elif sub_choice == "4":
            break  # Go back to the main menu
        else:
            print("Invalid choice. Please select a valid option.")

        input("Press Enter to continue...")

def unit_submenu(unit_ip):
    """
    Display a sub-menu for a specific unit with options to send a message, shutdown, adjust volume, or go back.
    """
    while True:
        print("\n--- Unit Options ---")
        print(f"IP Address: {unit_ip}")
        print("[1] Send Message")
        print("[2] Shutdown")
        print("[3] Adjust Speaker Volume")
        print("[4] Back to Main Menu")
        sub_choice = input("Enter your choice (1-4): ")

        if sub_choice == "1":
            message = input("Enter the message to send: ")
            send_message(message, unit_ip)
        elif sub_choice == "2":
            shutdown_unit(unit_ip)
        elif sub_choice == "3":
            try:
                volume = int(input("Enter volume percentage (0-100): "))
                if 0 <= volume <= 100:
                    set_unit_volume(unit_ip, volume)
                    print(f"Volume set to {volume}% sent to {unit_ip}")
                else:
                    print("Please enter a value between 0 and 100")
            except ValueError:
                print("Please enter a valid number")
        elif sub_choice == "4":
            break  # Go back to the main menu
        else:
            print("Invalid choice. Please select a valid option.")

        input("Press Enter to continue...")

def display_menu():
    """
    Display the menu options for the sender program.
    """
    print("\n--- Sender Menu ---")
    print("[1] Unit1 = 192.168.1.19")
    print("[2] Unit2 = 192.168.1.4")
    print("[3] Unit3 = 192.168.1.11")
    print("[4] Unit4 = 192.168.1.3")
    print("[5] Send to All Units")
    print("[6] Send to Custom IP")
    print("[7] Auto-Send to Open Ports")
    print("[8] Check Device Status")
    print("[9] Exit")

def main():
    """
    Main function to run the sender program.
    """
    while True:
        display_menu()
        choice = input("\nEnter your choice (1-9): ")

        if choice == "9":
            print("Exiting the program. Goodbye!")
            break

        if choice in UNITS:
            unit_ip = UNITS[choice]
            unit_submenu(unit_ip)
        elif choice == "5":
            action_submenu(send_to_all_units)
        elif choice == "6":
            custom_ip = input("Enter the custom IP address: ")
            custom_ip_submenu(custom_ip)
        elif choice == "7":
            network_range = "192.168.1.0/24"
            action_submenu(auto_send, network_range)
        elif choice == "8":
            check_device_status()
        else:
            print("Invalid choice. Please select a valid option.")

        input("Press Enter to continue...")

if __name__ == "__main__":
    main()

import os
import json
import platform
import socket
import uuid
import hashlib
import datetime
import subprocess
import zipfile

USER_PROFILES = ["Microsoft", "Ghost"]
BASE_DIR = None
for user in USER_PROFILES:
    candidate = os.path.join("C:/Users", user, "CIN", "CINLogs")
    if os.path.exists(candidate):
        BASE_DIR = candidate
        break
if BASE_DIR is None:
    BASE_DIR = os.path.expanduser("~/CIN/CINLogs")

REMINDER_LOG = os.path.join(BASE_DIR, "reminder_log.txt")
RAP_PATH = os.path.join(BASE_DIR, "rap.json")
LOG = os.path.join(BASE_DIR, "lastrun_log.txt")
PROFILE_ZIP = os.path.join(BASE_DIR, "microprofiles.zip")
RAP_STANDARD = os.path.join(BASE_DIR, "rap_standard.json")
RAP_SURFACE = os.path.join(BASE_DIR, "rap_SURFACEPRO3X-MXC.json")

STANDARD_PROFILE = {
    "system_name": platform.node().upper(),
    "os": platform.system(),
    "os_version": platform.version(),
    "architecture": platform.machine(),
    "hostname": socket.gethostname(),
    "ip_address": socket.gethostbyname(socket.gethostname()) if socket.gethostbyname(socket.gethostname()) else "Unknown",
    "mac_address": uuid.UUID(int=uuid.getnode()).hex[-12:],
    "serial_number": "SURFACE-STANDARD"
}

SURFACE_PROFILE = dict(STANDARD_PROFILE)
SURFACE_PROFILE["serial_number"] = "SURFACEPRO3X-MXC"

def set_reminder_note():
    try:
        os.makedirs(os.path.dirname(REMINDER_LOG), exist_ok=True)
        with open(REMINDER_LOG, 'a') as log_file:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[Reminder @ {timestamp}] Shower occurred before earlier outing. Reminder acknowledged.\n")
        print("Reminder note logged.")
    except Exception as e:
        print(f"Failed to write reminder note: {e}")

def log_last_run(status, system_hash):
    try:
        with open(LOG, 'w') as file:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"Last Run: {timestamp}\nStatus: {status}\nSystem Hash: {system_hash}\n")
    except Exception as e:
        print(f"Failed to write last run log: {e}")

def get_system_info():
    print("Collecting system information...")
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
    except Exception:
        ip_address = "Unknown"

    info = {
        "system_name": platform.node().upper(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "hostname": socket.gethostname(),
        "ip_address": ip_address,
        "mac_address": get_mac_address(),
        "serial_number": get_serial_number()
    }
    print("System information collected:", json.dumps(info, indent=2))
    return info

def get_mac_address():
    print("Retrieving MAC address...")
    try:
        mac = uuid.getnode()
        if (mac >> 40) % 2:
            raise ValueError
        mac_addr = ':'.join(f'{(mac >> ele) & 0xff:02x}' for ele in range(40, -1, -8))
        print(f"MAC address: {mac_addr}")
        return mac_addr
    except Exception:
        return "Unknown"

def get_serial_number():
    print("Retrieving serial number...")
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output("wmic bios get serialnumber", shell=True, stderr=subprocess.DEVNULL).decode(errors='ignore').splitlines()
            serial = next((line.strip() for line in output if line.strip() and "SerialNumber" not in line), "Unknown")
            return serial
        elif platform.system() == "Linux":
            path = "/sys/class/dmi/id/product_serial"
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read().strip()
        return "Unsupported"
    except Exception:
        return "Unknown"

def validate_microprofile(system_info):
    print("Validating RAP against system information...")
    if not os.path.isfile(RAP_PATH):
        print(f"RAP file not found at {RAP_PATH}")
        return False
    try:
        with open(RAP_PATH, 'r') as file:
            rap = json.load(file)
    except Exception:
        return False

    keys = ["system_name", "serial_number", "ip_address", "mac_address", "os", "architecture"]
    for key in keys:
        if key not in rap:
            return False
        rap_val = rap.get(key, "")
        sys_val = system_info.get(key, "")
        if key == "system_name":
            if sys_val != rap_val.upper():
                return False
        elif rap_val != sys_val:
            return False
    return True

def generate_system_hash(system_info):
    print("Generating system hash...")
    try:
        hash_input = json.dumps(system_info, sort_keys=True).encode()
        return hashlib.sha256(hash_input).hexdigest()
    except Exception:
        return ""

def write_microprofiles():
    try:
        profiles = {
            "microprofile_standard.json": STANDARD_PROFILE,
            "microprofile_SURFACEPRO3X-MXC.json": SURFACE_PROFILE
        }
        with zipfile.ZipFile(PROFILE_ZIP, 'w') as zipf:
            for name, data in profiles.items():
                path = os.path.join(BASE_DIR, name)
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
                zipf.write(path, arcname=name)
        with open(RAP_STANDARD, 'w') as f:
            json.dump(STANDARD_PROFILE, f, indent=2)
        with open(RAP_SURFACE, 'w') as f:
            json.dump(SURFACE_PROFILE, f, indent=2)
        print(f"Microprofiles written and zipped to {PROFILE_ZIP}")
        print(f"RAP files written to: {RAP_STANDARD} and {RAP_SURFACE}")
    except Exception as e:
        print(f"Failed to write microprofiles: {e}")

def main():
    print("Launching Watchdog Core Validator...")
    set_reminder_note()
    system_info = get_system_info()
    system_hash = generate_system_hash(system_info)
    write_microprofiles()
    if validate_microprofile(system_info):
        print("System authorized.")
        print(f"System Hash: {system_hash}")
        log_last_run("AUTHORIZED", system_hash)
    else:
        print("System not authorized. Shutting down core features.")
        log_last_run("UNAUTHORIZED", system_hash)

if __name__ == "__main__":
    main()

import json
import subprocess


ALLOWED_COMMANDS = {
    "cpu": ["lscpu"],
    "memory": ["free", "-h"],
    "disk": ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MODEL,ROTA,TRAN"],
    "gpu": ["lspci"],
}


def run_safe_command(command_name):
    if command_name not in ALLOWED_COMMANDS:
        raise ValueError("This command is not allowed.")

    try:
        return subprocess.run(
            ALLOWED_COMMANDS[command_name],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
            shell=False
        )
    except FileNotFoundError:
        raise RuntimeError(f"The {command_name} tool is not installed.")
    except PermissionError:
        raise RuntimeError(f"Permission was denied for the {command_name} tool.")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"The {command_name} tool took too long to respond.")
    except subprocess.CalledProcessError:
        raise RuntimeError(f"The {command_name} tool could not complete.")


def get_cpu_info():
    result = run_safe_command("cpu")
    cpu_info = {}

    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            cpu_info[key.strip()] = value.strip()

    return cpu_info


def get_memory_info():
    result = run_safe_command("memory")
    memory_line = ""

    for line in result.stdout.splitlines():
        if line.startswith("Mem:"):
            memory_line = line
            break

    if not memory_line:
        return {}

    memory_values = memory_line.split()

    return {
        "total": memory_values[1],
        "used": memory_values[2],
        "available": memory_values[6]
    }


def get_disk_info():
    result = run_safe_command("disk")

    try:
        disk_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError("Disk information could not be read.")

    disks = []

    for device in disk_data["blockdevices"]:
        if device["type"] != "disk":
            continue

        model = device.get("model") or "Unknown"

        if "virtual disk" in model.lower():
            disk_type = "Unknown (virtual disk in WSL)"
        elif device.get("rota") in [0, "0", False]:
            disk_type = "SSD"
        elif device.get("rota") in [1, "1", True]:
            disk_type = "HDD"
        else:
            disk_type = "Unknown"

        transport = device.get("tran")

        if transport == "nvme":
            nvme_status = "Yes"
        elif transport:
            nvme_status = "No"
        else:
            nvme_status = "Unknown"

        disks.append({
            "name": device.get("name", "Unknown"),
            "size": device.get("size", "Unknown"),
            "model": model,
            "type": disk_type,
            "nvme": nvme_status
        })

    return disks


def get_gpu_info():
    result = run_safe_command("gpu")

    for line in result.stdout.splitlines():
        if "VGA" in line or "3D controller" in line or "Display controller" in line:
            if "Microsoft Corporation" in line:
                return {
                    "device": "Virtual GPU exposed by WSL",
                    "details": line,
                    "note": "WSL cannot confirm the physical GPU model."
                }

            return {
                "device": line,
                "details": line,
                "note": ""
            }

    return {
        "device": "Not available",
        "details": "No GPU device was found by lspci.",
        "note": ""
    }


def main():
    try:
        cpu_info = get_cpu_info()
        memory_info = get_memory_info()
        disk_info = get_disk_info()
        gpu_info = get_gpu_info()

        print("\nCPU Information")
        print("----------------")
        print(f"Model: {cpu_info.get('Model name', 'Not available')}")
        print(f"Architecture: {cpu_info.get('Architecture', 'Not available')}")
        print(f"Logical processors: {cpu_info.get('CPU(s)', 'Not available')}")
        print(f"Cores: {cpu_info.get('Core(s) per socket', 'Not available')}")

        print("\nMemory Information")
        print("------------------")
        print(f"Total RAM: {memory_info.get('total', 'Not available')}")
        print(f"Used RAM: {memory_info.get('used', 'Not available')}")
        print(f"Available RAM: {memory_info.get('available', 'Not available')}")

        print("\nDisk Information")
        print("----------------")

        if not disk_info:
            print("No disk information available.")
        else:
            for disk in disk_info:
                print(f"\nName: {disk['name']}")
                print(f"Size: {disk['size']}")
                print(f"Model: {disk['model']}")
                print(f"Storage type: {disk['type']}")
                print(f"NVMe: {disk['nvme']}")

        print("\nGPU Information")
        print("---------------")
        print(f"Device: {gpu_info.get('device', 'Not available')}")
        print(f"Details: {gpu_info.get('details', 'Not available')}")

        if gpu_info.get("note"):
            print(f"Note: {gpu_info['note']}")

    except (RuntimeError, ValueError) as error:
        print(f"Could not read hardware information: {error}")


if __name__ == "__main__":
    main()

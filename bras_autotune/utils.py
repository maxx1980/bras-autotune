import os
import subprocess

# Импортируем ВСЕ функции из обновлённого nic.py
from bras_autotune.nic import (
    list_physical_interfaces,
    get_interface_queues,
    get_interface_ring,
    get_interface_txqueuelen,
    get_interface_driver,
    get_interface_fw,
    get_interface_speed,
    get_interface_pci,
    get_interface_lnksta,
)


# =====================================================================
# 1. Сбор общей системной информации (CPU, NUMA, IRQ, интерфейсы)
# =====================================================================
def collect_system_info():
    info = {}

    # CPU count
    info["cpu_cores"] = os.cpu_count()

    # Interfaces
    interfaces = list_physical_interfaces()
    info["interfaces"] = interfaces

    # NUMA nodes
    try:
        out = subprocess.check_output(["lscpu", "-p=NODE,CPU"]).decode()
        nodes = {}
        for line in out.splitlines():
            if line.startswith("#"):
                continue
            node, cpu = line.split(",")
            node = int(node)
            cpu = int(cpu)
            nodes.setdefault(node, []).append(cpu)
        info["numa_nodes"] = nodes
    except Exception:
        info["numa_nodes"] = {"0": list(range(info["cpu_cores"]))}

    # IRQ count
    try:
        irq = subprocess.check_output("ls /proc/irq | wc -l", shell=True).decode().strip()
        info["irq_count"] = int(irq)
    except Exception:
        info["irq_count"] = 0

    # Ring buffers
    info["rings"] = {
        iface: get_interface_ring(iface) or "not supported"
        for iface in interfaces
    }

    # RX/TX queues
    info["queues"] = {
        iface: get_interface_queues(iface)
        for iface in interfaces
    }

    # TX queue length
    info["interface_txqueuelen"] = {
        iface: get_interface_txqueuelen(iface)
        for iface in interfaces
    }

    # Driver
    info["driver"] = {
        iface: get_interface_driver(iface)
        for iface in interfaces
    }

    # Firmware
    info["fw"] = {
        iface: get_interface_fw(iface)
        for iface in interfaces
    }

    # PCIe info
    pcie = {}
    for iface in interfaces:
        pci = get_interface_pci(iface)
        lnksta = get_interface_lnksta(iface)
        pcie[iface] = {"pci": pci, "lnksta": lnksta}

    info["pcie"] = pcie

    return info


# =====================================================================
# 2. Полная статика для TUI (интерфейсы + health + needs_tuning)
def get_all_interfaces_stats():
    try:
        interfaces = list_physical_interfaces()
        result = {}

        for iface in interfaces:

            queues = get_interface_queues(iface)
            ring = get_interface_ring(iface)
            txq = get_interface_txqueuelen(iface)
            driver = get_interface_driver(iface)
            fw = get_interface_fw(iface)
            speed_raw = get_interface_speed(iface)
            pci_addr = get_interface_pci(iface)
            pcie_status = get_interface_lnksta(iface)

            # Если что-то None — заменяем безопасным значением
            if queues is None:
                queues = {"rx_cur": 0, "tx_cur": 0}

            if ring is None:
                ring = {"rx_cur": 0, "rx_max": 0, "tx_cur": 0, "tx_max": 0}

            if pcie_status is None:
                pcie_status = {"speed": None, "width": None}

            # HEALTH
            health = {}

            # Buffers
            health["buffers"] = (
                "OK" if ring.get("rx_cur", 0) >= 512 else "NOT_OK"
            )

            # PCIe presence
            health["pci"] = (
                "OK" if pcie_status.get("width") else "NOT_OK"
            )

            # Firmware
            health["fw"] = (
                "OK" if fw not in (None, "", "unknown") else "NOT_OK"
            )

            # Driver
            health["driver"] = (
                "OK" if driver not in (None, "", "unknown") else "NOT_OK"
            )

            # Queues
            health["queues"] = (
                "OK" if queues.get("rx_cur", 0) > 0 else "NOT_OK"
            )

            # Speed
            speed_flag = "OK"
            if speed_raw in (None, "unknown", "down"):
                speed_flag = "NOT_OK"

            health["speed"] = speed_flag

            # PCIe speed
            width = pcie_status.get("width")
            if width is None:
                health["pcie_speed"] = "NOT_OK"
            else:
                try:
                    w = int(width.replace("x", ""))
                    health["pcie_speed"] = "OK" if w >= 4 else "NOT_OK"
                except:
                    health["pcie_speed"] = "NOT_OK"

            # PCIe generation
            speed = pcie_status.get("speed")
            if speed is None:
                health["pcie_generation"] = "NOT_OK"
            else:
                try:
                    gt = float(speed.replace("GT/s", ""))
                    health["pcie_generation"] = "OK" if gt >= 8.0 else "NOT_OK"
                except:
                    health["pcie_generation"] = "NOT_OK"

            needs_tuning = any(v == "NOT_OK" for v in health.values())

            result[iface] = {
                "speed": speed_raw,
                "driver": driver,
                "fw": fw,
                "ring_buffers": ring,
                "txqueuelen": txq,
                "pci_addr": pci_addr,
                "pcie_status": pcie_status,
                "queues": queues,
                "health": health,
                "needs_tuning": needs_tuning,
            }

        return result

    except Exception as e:
        print("ERROR in get_all_interfaces_stats:", e)
        return {}
# =====================================================================
# 3. Вспомогательная функция
# =====================================================================
def run(cmd):
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
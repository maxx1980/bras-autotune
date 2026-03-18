import os
import subprocess

# Импортируем ВСЕ функции из nic.py
from bras_autotune.nic import (
    list_physical_interfaces,
    get_ring_buffers,
    get_interface_queues,
    get_interface_txqueuelen,
    get_interface_driver,
    get_interface_fw,
    get_interface_speed,
    get_pci_from_ethtool,
    get_pcie_lnksta,
)


# -------------------------------------------------------------
#  СИСТЕМНАЯ ИНФОРМАЦИЯ (CPU, NUMA, IRQ, интерфейсы)
# -------------------------------------------------------------
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
    rings = {}
    for iface in interfaces:
        rb = get_ring_buffers(iface)
        rings[iface] = rb if rb is not None else "not supported"
    info["rings"] = rings

    # RX/TX queues
    info["queues"] = {iface: get_interface_queues(iface) for iface in interfaces}

    # TX queue length
    info["interface_txqueuelen"] = {
        iface: get_interface_txqueuelen(iface) for iface in interfaces
    }

    # Driver
    info["driver"] = {iface: get_interface_driver(iface) for iface in interfaces}

    # Firmware
    info["fw"] = {iface: get_interface_fw(iface) for iface in interfaces}

    # PCIe info
    pcie = {}
    for iface in interfaces:
        pci = get_pci_from_ethtool(iface)
        lnksta = get_pcie_lnksta(pci)
        pcie[iface] = {"pci": pci, "lnksta": lnksta}
    info["pcie"] = pcie

    return info


# -------------------------------------------------------------
#  ПОЛНАЯ СТАТИКА ДЛЯ TUI (интерфейсы, очереди, PCIe, драйверы)
# -------------------------------------------------------------
def get_all_interfaces_stats():
    """
    Собирает статическую информацию по всем физическим интерфейсам:
    - скорость
    - драйвер
    - прошивка
    - ring buffers
    - txqueuelen
    - PCIe адрес и статус
    - список RX/TX очередей
    """

    interfaces = list_physical_interfaces()
    result = {}

    for iface in interfaces:
        queues = get_interface_queues(iface)

        pci_addr = get_pci_from_ethtool(iface)
        pcie_status = get_pcie_lnksta(pci_addr) if pci_addr else None

        result[iface] = {
            "speed": get_interface_speed(iface),
            "driver": get_interface_driver(iface),
            "fw": get_interface_fw(iface),
            "ring_buffers": get_ring_buffers(iface),
            "txqueuelen": get_interface_txqueuelen(iface),
            "pci_addr": pci_addr,
            "pcie_status": pcie_status,
            "queues": queues,
        }

    return result


# -------------------------------------------------------------
#  ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ
# -------------------------------------------------------------
def run(cmd):
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
import os
import subprocess
#from bras_autotune.nic import list_physical_interfaces, get_ring_buffers, get_interface_queues, get_interface_txqueuelen
from bras_autotune.nic import *

def collect_system_info():
    info = {}

    # CPU count
    info["cpu_cores"] = os.cpu_count()

    # Interfaces
    info["interfaces"] = list_physical_interfaces()

    # NUMA
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
    except:
        info["numa_nodes"] = {"0": list(range(info["cpu_cores"]))}

    # IRQ count
    try:
        irq = subprocess.check_output("ls /proc/irq | wc -l", shell=True).decode().strip()
        info["irq_count"] = int(irq)
    except:
        info["irq_count"] = 0

    # Buffers
    rings = {}
    for iface in info["interfaces"]:
        rb = get_ring_buffers(iface)
        if rb is None:
            rings[iface] = "not supported"
        else:
            rings[iface] = rb  # ← уже строка!
    info["rings"] = rings

    # RX/TX queues
    queues = {}
    for iface in info["interfaces"]:
        queues[iface] = get_interface_queues(iface)
    info["queues"] = queues

    # TX queuesen

    txq = {}
    for iface in info["interfaces"]:
        txq[iface] = get_interface_txqueuelen(iface)

    info["interface_txqueuelen"] = txq
    # Diver

    drv = {}
    for iface in info["interfaces"]:
        drv[iface] = get_interface_driver(iface)

    info["driver"] = drv
    # fw

    fw = {}
    for iface in info["interfaces"]:
        fw[iface] = get_interface_fw(iface)

    info["fw"] = fw

    # pcistat

    info["pcie"] = {}

    for iface in info["interfaces"]:
        pci = get_pci_from_ethtool(iface)
        lnksta = get_pcie_lnksta(pci)

        info["pcie"][iface] = {
            "pci": pci,
            "lnksta": lnksta
        }


    return info   # ← ЭТО ОБЯЗАТЕЛЬНО

def run(cmd):
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()




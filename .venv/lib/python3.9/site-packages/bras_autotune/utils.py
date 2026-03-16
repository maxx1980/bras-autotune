import os
import subprocess
from bras_autotune.nic import list_physical_interfaces, get_ring_buffers, get_interface_queues, get_interface_txqueuelen
#from bras_autotune.nic import *

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

    txq = {}
    for iface in info["interfaces"]:
        txq[iface] = get_interface_txqueuelen(iface)

    # TX queuesen
    info["interface_txqueuelen"] = txq

    return info   # ← ЭТО ОБЯЗАТЕЛЬНО

def run(cmd):
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()




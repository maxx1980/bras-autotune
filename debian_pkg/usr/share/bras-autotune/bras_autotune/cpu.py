import os
import subprocess

def get_cpu_info():
    info = {}

    # Количество ядер
    info["cores"] = os.cpu_count()

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
        info["numa"] = nodes
    except:
        info["numa"] = {"0": list(range(info["cores"]))}

    # Частоты
    freqs = {}
    for cpu in range(info["cores"]):
        try:
            with open(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_cur_freq") as f:
                freqs[cpu] = int(f.read().strip())
        except:
            freqs[cpu] = None
    info["freqs"] = freqs

    return info
def hex_mask_from_cpu_list(cpus):
    mask = 0
    for cpu in cpus:
        mask |= 1 << cpu
    return format(mask, "x")

def cpu_range(start, end):
    return list(range(start, end + 1))

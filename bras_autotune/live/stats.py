import psutil
import os


def get_cpu_per_core():
    """Возвращает загрузку каждого ядра в процентах."""
    return psutil.cpu_percent(percpu=True)


def get_memory_usage():
    """Возвращает использование памяти в процентах."""
    return psutil.virtual_memory().percent


def get_cpu_count():
    """Возвращает количество физических ядер."""
    return psutil.cpu_count(logical=False)


def get_numa_nodes():
    """Возвращает количество NUMA-нод."""
    path = "/sys/devices/system/node"
    if os.path.exists(path):
        return len([d for d in os.listdir(path) if d.startswith("node")])
    return 1

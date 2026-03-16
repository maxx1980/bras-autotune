
import re
from bras_autotune.utils import run
from bras_autotune.cpu import cpu_range, hex_mask_from_cpu_list
import os

def list_physical_interfaces():
    interfaces = []
    for iface in os.listdir("/sys/class/net"):
        # пропускаем loopback
        if iface == "lo":
            continue

        # пропускаем виртуальные интерфейсы
        if not os.path.exists(f"/sys/class/net/{iface}/device"):
            continue

        interfaces.append(iface)

    return interfaces

def nic_max_queues(ifname):
    try:
        out = run(["ethtool", "-l", ifname])
    except Exception:
        return None

    for line in out.splitlines():
        if "Combined:" in line:
            try:
                return int(line.split()[-1])
            except ValueError:
                return None
    return None

def detect_irqs_for_if(ifname):
    irqs = []
    with open("/proc/interrupts") as f:
        for line in f:
            if re.search(rf"\b{re.escape(ifname)}\b", line):
                irq = line.split(":")[0].strip()
                if irq.isdigit():
                    irqs.append(int(irq))
    return irqs

def sync_cores_with_nic_queues(cfg):
    """
    Синхронизирует количество очередей NIC с количеством data-plane ядер.
    Если очередей меньше — уменьшаем data_cores.
    Если очередей больше — оставляем как есть.
    """

    # WAN
    wan = cfg["if_wan"]
    bras = cfg["if_bras"]

    # Получаем количество очередей
    rxq_wan = cfg["rxq_wan"]
    rxq_bras = cfg["rxq_bras"]

    data_cores = cfg["data_cores"]

    # WAN
    if rxq_wan < data_cores:
        print(f"⚠ WAN NIC имеет только {rxq_wan} очередей — уменьшаем DATA-plane ядра до {rxq_wan}")
        data_cores = rxq_wan

    # BRAS
    if rxq_bras < data_cores:
        print(f"⚠ BRAS NIC имеет только {rxq_bras} очередей — уменьшаем DATA-plane ядра до {rxq_bras}")
        data_cores = rxq_bras

    # Пересчитываем списки CPU
    cfg["data_cores"] = data_cores
    cfg["data_cpu_list"] = list(range(data_cores))
    cfg["ctrl_cpu_list"] = list(range(data_cores, os.cpu_count()))

    # Пересчитываем маску
    cfg["data_mask_hex"] = format((1 << data_cores) - 1, "x")

    return cfg

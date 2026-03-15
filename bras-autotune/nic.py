
import re
from bras_autotune.utils import run
from bras_autotune.cpu import cpu_range, hex_mask_from_cpu_list

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
    if_bras = cfg["if_bras"]
    if_wan = cfg["if_wan"]
    total = cfg["total_cores"]
    data = cfg["data_cores"]
    ctrl = cfg["ctrl_cores"]

    max_bras = nic_max_queues(if_bras)
    if max_bras is None:
        raise SystemExit("Не удалось определить очереди BRAS NIC")

    if data > max_bras:
        print(f"Data-plane ядер ({data}) > очередей BRAS ({max_bras}), уменьшаю.")
        data = max_bras
        ctrl = total - data

    max_wan = nic_max_queues(if_wan)
    if max_wan is None:
        raise SystemExit("Не удалось определить очереди WAN NIC")

    rxq_bras = data
    rxq_wan = min(data, max_wan)

    data_list = cpu_range(0, data - 1)
    ctrl_list = cpu_range(data, total - 1)

    cfg.update(
        data_cores=data,
        ctrl_cores=ctrl,
        data_cpu_list=data_list,
        ctrl_cpu_list=ctrl_list,
        data_mask_hex=hex_mask_from_cpu_list(data_list),
        ctrl_mask_hex=hex_mask_from_cpu_list(ctrl_list),
        rxq_bras=rxq_bras,
        rxq_wan=rxq_wan,
    )
    return cfg

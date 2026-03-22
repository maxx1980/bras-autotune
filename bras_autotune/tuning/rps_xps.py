import os
from typing import Dict, List
from typing import Optional
from bras_autotune.cpu import get_cpu_info, hex_mask_from_cpu_list


def get_rps_mask_from_cpu_info() -> str:
    info = get_cpu_info()
    cores = info.get("cores", 1)

    # список CPU: [0, 1, 2, ...]
    cpu_list = list(range(cores))

    # генерируем hex‑маску
    return hex_mask_from_cpu_list(cpu_list)

def read_sysfs(path: str) -> Optional[str]:
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return None


def get_rps_xps(iface: str) -> Dict:
    """
    Возвращает структуру:
    {
        "rps": { "rx-0": "ff", "rx-1": "00", ... },
        "xps": { "tx-0": "01", "tx-1": "02", ... }
    }
    """
    base = f"/sys/class/net/{iface}/queues"
    data = {"rps": {}, "xps": {}}

    if not os.path.isdir(base):
        return data

    for q in os.listdir(base):
        qpath = os.path.join(base, q)

        # RPS
        rps_file = os.path.join(qpath, "rps_cpus")
        if os.path.isfile(rps_file):
            val = read_sysfs(rps_file)
            data["rps"][q] = val if val else "0"

        # XPS
        xps_file = os.path.join(qpath, "xps_cpus")
        if os.path.isfile(xps_file):
            val = read_sysfs(xps_file)
            data["xps"][q] = val if val else "0"

    return data


# ---------------------------------------------------------
#  РЕКОМЕНДАЦИИ ДЛЯ WAN
# ---------------------------------------------------------

def recommend_rps_xps_wan(iface: str, rpsxps: Dict) -> List[str]:
    """
    WAN любит включённый XPS.
    """
    maskhex = get_rps_mask_from_cpu_info()

    rec = []

    # RPS
    for q, mask in rpsxps["rps"].items():
        if mask != "0":
            rec.append(
                f"RPS off {q}: [white]echo 0 > /sys/class/net/{iface}/queues/{q}/rps_cpus[/white]"
            )
        

    # XPS
    for q, mask in rpsxps["xps"].items():
        if mask != maskhex:
            rec.append(
                f"XPS on {q}: [white]echo {maskhex} > /sys/class/net/{iface}/queues/{q}/xps_cpus[/white]"
            )

    if not rec:
        rec.append("RPS/XPS оптимизированы для WAN.")

    return rec


# ---------------------------------------------------------
#  РЕКОМЕНДАЦИИ ДЛЯ PPPoE
# ---------------------------------------------------------

def recommend_rps_xps_pppoe(iface: str, rpsxps: Dict) -> List[str]:
    """
    PPPoE лучше работает с включенными RPS/XPS (меньше latency).
    """
    mask = get_rps_mask_from_cpu_info()
    maskhex = get_rps_mask_from_cpu_info()
    rec = []

    # RPS
    for q, mask in rpsxps["rps"].items():
        if mask != maskhex:
            rec.append(
                f"RPS on {q}: [white]echo {maskhex} > /sys/class/net/{iface}/queues/{q}/rps_cpus[/white]"
            )
    # XPS
    for q, mask in rpsxps["xps"].items():
        if mask != maskhex:
            rec.append(
                f"XPS on {q}: [white]echo {maskhex} > /sys/class/net/{iface}/queues/{q}/xps_cpus[/white]"
            )

    if not rec:
        rec.append("RPS/XPS оптимизированы для PPPoE.")

    return rec


# ---------------------------------------------------------
#  ОБЩАЯ ФУНКЦИЯ
# ---------------------------------------------------------

def get_rps_xps_recommendations(iface: str, mode: str) -> List[str]:
    rpsxps = get_rps_xps(iface)

    if mode == "wan":
        return recommend_rps_xps_wan(iface, rpsxps)

    if mode == "pppoe":
        return recommend_rps_xps_pppoe(iface, rpsxps)

    return ["Неизвестный режим оптимизации."]

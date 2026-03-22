from typing import Optional
import subprocess

def run_ethtool_k(iface: str) -> Optional[str]:
    try:
        return subprocess.check_output(
            ["/sbin/ethtool", "-k", iface],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None

def parse_offloads(output: str) -> dict:
    """
    Парсит вывод ethtool -k в словарь:
    {
        "gro": True/False,
        "lro": True/False,
        "tso": True/False,
        "gso": True/False,
        "rx-checksumming": True/False,
        ...
    }
    """
    offloads = {}

    for line in output.splitlines():
        line = line.strip().lower()

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value.startswith("on"):
            offloads[key] = True
        elif value.startswith("off"):
            offloads[key] = False

    return offloads
# ---------------------------------------------------------
#  РЕКОМЕНДАЦИИ ДЛЯ WAN (ETHERNET)
# ---------------------------------------------------------

def optimize_wan_offloads(iface: str, off: dict) -> list[str]:
    """
    Рекомендации для WAN-интерфейса (Ethernet).
    WAN любит offloads включённые.
    """
    rec = []

    # GRO
    if not off.get("generic-receive-offload", True):
        rec.append(f"Включите GRO: [white]ethtool -K {iface} gro on[/white]")

    # LRO
    if not off.get("large-receive-offload", True):
        rec.append(f"Включите LRO: [white]ethtool -K {iface} lro on[/white]")

    # TSO
    if not off.get("tcp-segmentation-offload", True):
        rec.append(f"Включите TSO: [white]ethtool -K {iface} tso on[/white]")

    # GSO
    if not off.get("generic-segmentation-offload", True):
        rec.append(f"Включите GSO: [white]ethtool -K {iface} gso on[/white]")

    # RX checksum
    if not off.get("rx-checksumming", True):
        rec.append(f"Включите RX checksum: [white]ethtool -K {iface} rx on[/white]")

    # TX checksum
    if not off.get("tx-checksumming", True):
        rec.append(f"Включите TX checksum: [white]ethtool -K {iface} tx on[/white]")

    if not rec:
        rec.append("WAN интерфейс оптимизирован. Изменений не требуется.")

    return rec

def get_interface_offloads(iface: str) -> dict:
    """Возвращает словарь offload-настроек интерфейса."""
    out = run_ethtool_k(iface)
    if not out:
        return {}

    return parse_offloads(out)





# ---------------------------------------------------------
#  РЕКОМЕНДАЦИИ ДЛЯ PPPoE
# ---------------------------------------------------------

def optimize_pppoe_offloads(iface: str, off: dict) -> list[str]:
    """
    Рекомендации для PPPoE.
    PPPoE НЕ любит offloads — они ломают MTU и фрагментацию.
    """
    rec = []

    # GRO
    if off.get("generic-receive-offload", False):
        rec.append(f"Отключите GRO: [white]ethtool -K {iface} gro off[/white]")

    # LRO
    if off.get("large-receive-offload", False):
        rec.append(f"Отключите LRO: [white]ethtool -K {iface} lro off[/white]")

    # TSO
    if off.get("tcp-segmentation-offload", False):
        rec.append(f"Отключите TSO: [white]ethtool -K {iface} tso off[/white]")

    # GSO
    if off.get("generic-segmentation-offload", False):
        rec.append(f"Отключите GSO: [white]ethtool -K {iface} gso off[/white]")

    # RX checksum
    if off.get("rx-checksumming", False):
        rec.append(f"Отключите RX checksum: [white]ethtool -K {iface} rx off[/white]")

    # TX checksum
    if off.get("tx-checksumming", False):
        rec.append(f"Отключите TX checksum: [white]ethtool -K {iface} tx off[/white]")

    if not rec:
        rec.append("PPPoE интерфейс оптимизирован. Изменений не требуется.")

    return rec


# ---------------------------------------------------------
#  ОБЩАЯ ФУНКЦИЯ
# ---------------------------------------------------------

def get_offload_recommendations(iface: str, mode: str) -> list[str]:
    """
    mode = "wan" или "pppoe"
    """
    off = get_interface_offloads(iface)

    if mode == "wan":
        return optimize_wan_offloads(iface, off)

    if mode == "pppoe":
        return optimize_pppoe_offloads(iface, off)

    return ["Неизвестный режим оптимизации."]
import os
import subprocess


# ============================================================
# 1. Безопасный вызов ethtool
# ============================================================
def run_ethtool(args):
    """
    Безопасный вызов ethtool.
    Возвращает строку или None, если команда не поддерживается.
    """
    ETHTOOL = "/usr/sbin/ethtool"

    if not os.path.exists(ETHTOOL):
        return None

    try:
        output = subprocess.check_output(
            [ETHTOOL] + args,
            stderr=subprocess.STDOUT
        ).decode()
        return output
    except Exception:
        return None


# ============================================================
# 2. Фильтрация физических интерфейсов
# ============================================================
def list_physical_interfaces():
    """
    Возвращает список ТОЛЬКО физических интерфейсов.
    Фильтрует VLAN, виртуальные, подинтерфейсы, lo, ifb и т.д.
    """
    ifaces = []

    for iface in os.listdir("/sys/class/net"):
        name = iface.lower()

        # loopback
        if name == "lo":
            continue

        # ifb — виртуальные интерфейсы
        if name.startswith("ifb"):
            continue

        # VLAN по имени: vlan100
        if name.startswith("vlan"):
            continue

        # VLAN по формату: eth0.100
        if "." in name:
            continue

        # Подинтерфейсы: eth0:1
        if ":" in name:
            continue

        # Подинтерфейсы с @: ens192.50@ens192
        if "@" in name:
            continue

        # Виртуальные интерфейсы
        if name.startswith(("docker", "veth", "br", "virbr", "tap", "tun")):
            continue

        # Bond slaves
        if os.path.exists(f"/sys/class/net/{iface}/master"):
            continue

        # Физический интерфейс должен иметь /device
        if not os.path.exists(f"/sys/class/net/{iface}/device"):
            continue

        ifaces.append(iface)

    return ifaces


# ============================================================
# 3. Очереди интерфейса
# ============================================================
def get_interface_queues(iface):
    """
    Возвращает структуру:
    {
        "rx_cur": int,
        "tx_cur": int,
        "rx_max": int | None,
        "tx_max": int | None
    }
    """
    qpath = f"/sys/class/net/{iface}/queues"
    if not os.path.exists(qpath):
        return {"rx_cur": 0, "tx_cur": 0, "rx_max": None, "tx_max": None}

    q = sorted(os.listdir(qpath))
    rx_cur = len([x for x in q if x.startswith("rx-")])
    tx_cur = len([x for x in q if x.startswith("tx-")])

    out = run_ethtool(["-l", iface])
    rx_max = tx_max = combined_max = None

    if out:
        for line in out.splitlines():
            line = line.strip().lower()

            if line.startswith("combined:") and "current" not in line:
                try:
                    combined_max = int(line.split()[1])
                except:
                    pass

            if line.startswith("rx:") and "current" not in line:
                val = line.split()[1]
                if val.isdigit():
                    rx_max = int(val)

            if line.startswith("tx:") and "current" not in line:
                val = line.split()[1]
                if val.isdigit():
                    tx_max = int(val)

    if rx_max is None:
        rx_max = combined_max
    if tx_max is None:
        tx_max = combined_max

    return {
        "rx_cur": rx_cur,
        "tx_cur": tx_cur,
        "rx_max": rx_max,
        "tx_max": tx_max,
    }


# ============================================================
# 4. Скорость интерфейса
# ============================================================
def get_interface_speed(iface):
    """
    Возвращает скорость интерфейса из нескольких источников:
    1) ethtool (основной источник)
    2) /sys/class/net/<iface>/speed
    3) /sys/class/net/<iface>/operstate
    """

    # ---------------------------------------------------------
    # 1. Попытка получить скорость через ethtool
    # ---------------------------------------------------------
    out = run_ethtool(["-i", iface])
    if out:
        for line in out.splitlines():
            if "speed" in line.lower():
                val = line.split(":", 1)[1].strip()
                if val and "unknown" not in val.lower():
                    return val

    # ---------------------------------------------------------
    # 2. Попытка получить скорость через sysfs
    # ---------------------------------------------------------
    sys_speed = f"/sys/class/net/{iface}/speed"
    if os.path.exists(sys_speed):
        try:
            with open(sys_speed) as f:
                val = f.read().strip()
                # speed может быть "-1" или "unknown"
                if val.isdigit() and int(val) > 0:
                    return f"{val}Mb/s"
        except:
            pass

    # ---------------------------------------------------------
    # 3. Проверка operstate (up/down)
    # ---------------------------------------------------------
    oper = f"/sys/class/net/{iface}/operstate"
    if os.path.exists(oper):
        try:
            with open(oper) as f:
                state = f.read().strip()
                if state == "down":
                    return "down"
                if state == "unknown":
                    return "unknown"
        except:
            pass

    # ---------------------------------------------------------
    # 4. Если ничего не удалось определить
    # ---------------------------------------------------------
    return "unknown"

# ============================================================
# 5. Драйвер и прошивка
# ============================================================
def get_interface_driver(iface):
    out = run_ethtool(["-i", iface])
    if out is None:
        return None

    for line in out.splitlines():
        if "driver:" in line.lower():
            return line.split(":", 1)[1].strip()

    return None


def get_interface_fw(iface):
    out = run_ethtool(["-i", iface])
    if out is None:
        return "unknown"

    for line in out.splitlines():
        line_low = line.lower().strip()

        if line_low.startswith("firmware-version:"):
            value = line.split(":", 1)[1].strip()
            if value == "" or value.lower() == "n/a":
                return "unknown"
            return value

    return "unknown"


# ============================================================
# 6. Buffers (ring)
# ============================================================
def get_interface_ring(iface):
    out = run_ethtool(["-g", iface])
    if out is None:
        return None

    rx_cur = tx_cur = rx_max = tx_max = None

    for line in out.splitlines():
        line = line.strip().lower()

        if line.startswith("rx:") and rx_max is None:
            try:
                rx_max = int(line.split()[1])
            except:
                pass

        if line.startswith("tx:") and tx_max is None:
            try:
                tx_max = int(line.split()[1])
            except:
                pass

        if "current hardware settings" in line:
            continue

        if line.startswith("rx:") and rx_cur is None and rx_max is not None:
            try:
                rx_cur = int(line.split()[1])
            except:
                pass

        if line.startswith("tx:") and tx_cur is None and tx_max is not None:
            try:
                tx_cur = int(line.split()[1])
            except:
                pass

    if rx_cur is None or tx_cur is None:
        return None

    return {
        "rx_cur": rx_cur,
        "rx_max": rx_max,
        "tx_cur": tx_cur,
        "tx_max": tx_max,
    }


# ============================================================
# 7. TX queue length
# ============================================================
def get_interface_txqueuelen(iface):
    path = f"/sys/class/net/{iface}/tx_queue_len"

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as f:
            return int(f.read().strip())
    except:
        return None


# ============================================================
# 8. PCIe
# ============================================================
def get_interface_pci(iface):
    out = run_ethtool(["-i", iface])
    if out is None:
        return None

    for line in out.splitlines():
        if "bus-info:" in line.lower():
            return line.split(":", 1)[1].strip()

    return None


def get_interface_lnksta(iface):
    addr = get_interface_pci(iface)
    if addr is None:
        return None

    base = f"/sys/bus/pci/devices/{addr}"

    try:
        with open(f"{base}/current_link_speed") as f:
            speed = f.read().strip()

        with open(f"{base}/current_link_width") as f:
            width = f.read().strip()

        with open(f"{base}/max_link_speed") as f:
            max_speed = f.read().strip()

        with open(f"{base}/max_link_width") as f:
            max_width = f.read().strip()

    except Exception:
        return None

    return {
        "speed": speed,
        "width": width,
        "max_speed": max_speed,
        "max_width": max_width,
    }
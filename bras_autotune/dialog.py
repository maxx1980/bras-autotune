from dialog import Dialog
from bras_autotune.utils import collect_system_info
from bras_autotune.nic import list_physical_interfaces
from bras_autotune.cpu import get_cpu_info


# -----------------------------
# Цветовая подсветка
# -----------------------------
def colorize(cur, maxv):
    """
    Возвращает строку с цветом:
    - красный жирный, если cur < maxv
    - зелёный жирный, если cur == maxv
    - без цвета, если maxv неизвестен
    """
    if maxv is None or maxv == "unknown":
#        return f"{cur} (max {maxv})"
        return f"\\Z1\\Zb{cur}\\Zn (max {maxv})"   # красный жирный

    if cur < maxv:
        return f"\\Z1\\Zb{cur}\\Zn (max {maxv})"   # красный жирный
    else:
        return f"\\Z4\\Zb{cur}\\Zn (max {maxv})"   # синий yжирный
def colorize_txq(value):
    """
    Подсветка txqueuelen:
    - красный жирный, если < 10000
    - тёмно-синий жирный, если >= 10000
    """
    if value is None:
        return "unknown"

    if value < 10000:
        return f"\\Z1\\Zb{value}\\Zn"   # красный жирный
    else:
        return f"\\Z4\\Zb{value}\\Zn"   # тёмно-синий жирный


# -----------------------------
# Главный инсталлер
# -----------------------------
def bras_autotune_installer():
    d = Dialog(dialog="dialog")
    d.set_background_title("BRAS AUTOTUNE")
    d.add_persistent_args(["--colors"])   # ВКЛЮЧАЕМ ЦВЕТА

    cfg = {}

    while True:
        code, choice = d.menu(
            "Главное меню",
            choices=[
                ("1", "Сбор информации"),
                ("2", "Настройка системы"),
                ("3", "Генерация конфигов"),
                ("4", "Выход"),
            ],
            width=60, height=20
        )

        if code != d.OK:
            return None

        if choice == "1":
            info_menu(d)

        elif choice == "2":
            system_menu(d, cfg)

        elif choice == "3":
            generate_menu(d, cfg)

        elif choice == "4":
            return None


# -----------------------------
# 1. Сбор информации
# -----------------------------
def info_menu(d):
    info = collect_system_info()

    text = (
        "СИСТЕМНАЯ ИНФОРМАЦИЯ\n"
        "====================\n\n"
        f"CPU cores: {info['cpu_cores']}\n"
        f"NUMA nodes: {info['numa_nodes']}\n"
        f"Interfaces: {', '.join(info['interfaces'])}\n"
        f"IRQ count: {info['irq_count']}\n\n"
        "Интерфейсы:\n"
    )

    for iface in info["interfaces"]:
        drv = info["driver"].get(iface)
        fw = info["fw"].get(iface)

        text += f"  {iface} driver: {drv} firmware: {fw}\n"

        # TX queue
        txq = info["interface_txqueuelen"].get(iface)
        txq = colorize_txq(txq)
        text += f"        TXqlen: {txq}\n"

        # PCIe
        lnk = info["pcie"][iface]["lnksta"]

        speed = lnk["speed"]
        width = int(lnk["width"])
        max_speed = lnk["max_speed"]
        max_width = int(lnk["max_width"])

        speed_colored = colorize(speed, max_speed)
        width_colored = colorize(width, max_width)

        text += f"        PCIe: Width {width_colored}\n"
        text += f"              Speed {speed_colored}\n"

        # Очереди
        qc = info["queues"].get(iface)
        if isinstance(qc, dict):
            rx_str = colorize(qc["rx_cur"], qc["rx_max"])
            tx_str = colorize(qc["tx_cur"], qc["tx_max"])
            text += f"        Очереди: RX {rx_str}, TX {tx_str}\n"
        else:
            text += f"        Очереди: {qc}\n"

        # Буферы
        rb = info["rings"].get(iface, "not supported")
        if rb != "not supported":
            try:
                rx_part, tx_part = rb.split(",")
                rx_cur, rx_max = map(int, rx_part.strip()[3:].split("/"))
                tx_cur, tx_max = map(int, tx_part.strip()[3:].split("/"))

                rx_buf = colorize(rx_cur, rx_max)
                tx_buf = colorize(tx_cur, tx_max)

                text += f"        Буферы: RX {rx_buf}, TX {tx_buf}\n\n"
            except:
                text += f"        Буферы: {rb}\n\n"
        else:
            text += f"        Буферы: \\Z1\\Zbnot supported\\Zn\n\n"

#    # Добавляем отступ в 8 пробелов
#    indented = "\n".join("        " + line for line in text.splitlines())

    d.msgbox(text, width=100, height=30)


# -----------------------------
# 2. Настройка системы
# -----------------------------
def system_menu(d, cfg):
    while True:
        code, choice = d.menu(
            "Настройка системы",
            choices=[
                ("1", "Настройка CPU"),
                ("2", "Настройка Data Plane"),
                ("3", "Настройка Control Plane"),
                ("back", "Назад"),
            ],
            width=60, height=20
        )

        if code != d.OK or choice == "back":
            return

        if choice == "1":
            cpu_setup(d, cfg)
        elif choice == "2":
            dataplane_setup(d, cfg)
        elif choice == "3":
            controlplane_setup(d, cfg)


# -----------------------------
# 2.1 Настройка CPU
# -----------------------------
def cpu_setup(d, cfg):
    total = get_cpu_info()["cores"]

    code, cores = d.inputbox(
        f"Сколько ядер выделить под DATA-plane? (всего {total})",
        width=60
    )
    if code == d.OK:
        cores = int(cores)
        cfg["data_cores"] = cores
        cfg["data_cpu_list"] = list(range(cores))
        cfg["ctrl_cpu_list"] = list(range(cores, total))
        d.msgbox(f"DATA-plane: {cfg['data_cpu_list']}\nCTRL-plane: {cfg['ctrl_cpu_list']}")


# -----------------------------
# 2.2 Настройка Data Plane
# -----------------------------
def dataplane_setup(d, cfg):
    ifaces = list_physical_interfaces()

    if not ifaces:
        d.msgbox("Не найдено ни одного физического интерфейса!", width=50)
        return

    code, wan = d.menu(
        "Выберите WAN интерфейс:",
        choices=[(i, "") for i in ifaces],
        width=60, height=20
    )
    if code != d.OK:
        return

    bras_list = [i for i in ifaces if i != wan]

    if not bras_list:
        d.msgbox("Нет доступных интерфейсов для BRAS!", width=50)
        return

    code, bras = d.menu(
        "Выберите BRAS интерфейс:",
        choices=[(i, "") for i in bras_list],
        width=60, height=20
    )
    if code != d.OK:
        return

    cfg["if_wan"] = wan
    cfg["if_bras"] = bras

    d.msgbox(f"WAN интерфейс:  {wan}\nBRAS интерфейс: {bras}", width=50)


# -----------------------------
# 2.3 Настройка Control Plane
# -----------------------------
def controlplane_setup(d, cfg):
    apps = [
        ("accel-ppp", "Перенести в Control Plane", False),
        ("pppoe-server", "Перенести в Control Plane", False),
        ("dnsmasq", "Перенести в Control Plane", False),
    ]

    code, selected = d.checklist(
        "Выберите процессы для Control Plane:",
        choices=apps,
        width=60,
        height=20,
        no_tags=False
    )

    if code != d.OK:
        return

    cfg["ctrl_apps"] = list(selected)

    if selected:
        d.msgbox("Выбрано:\n" + "\n".join(selected), width=50)
    else:
        d.msgbox("Ни один процесс не выбран.", width=50)


# -----------------------------
# 3. Генерация конфигов
# -----------------------------
def generate_menu(d, cfg):
    while True:
        code, choice = d.menu(
            "Генерация конфигов",
            choices=[
                ("1", "Настройка сохранения"),
                ("2", "Генерация"),
                ("back", "Назад"),
            ],
            width=60, height=20
        )

        if code != d.OK or choice == "back":
            return

        if choice == "1":
            save_setup(d, cfg)
        elif choice == "2":
            return cfg


def save_setup(d, cfg):
    code, out = d.menu(
        "Куда сохранить конфиги?",
        choices=[
            ("home", "~/bras-autotune"),
            ("tmp", "/tmp/bras-autotune"),
            ("etc", "/etc/network/interfaces.d"),
        ],
        width=60, height=20
    )
    if code == d.OK:
        cfg["out_dir"] = out
        cfg["etc_mode"] = (out == "/etc/network/interfaces.d")
        d.msgbox(f"Выбрано: {out}")

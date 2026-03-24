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
def info_menu(d):
    info = collect_system_info()

    # Список интерфейсов
    choices = [(iface, "") for iface in info["interfaces"]]

    while True:
        code, iface = d.menu(
            "Информация об интерфейсах",
            choices=choices,
            width=60,
            height=20
        )

        if code != d.OK:
            return

        # СРАЗУ открываем окно свойств
        show_interface_details(d, info, iface)
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

    choices = [(iface, "") for iface in info["interfaces"]]

    while True:
        code, iface = d.menu(
            "Информация об интерфейсах",
            choices=choices,
            width=60,
            height=20
        )

        if code != d.OK:
            return

        show_interface_main(d, info, iface)
def show_interface_main(d, info, iface):
    drv = info["driver"].get(iface)
    fw = info["fw"].get(iface)
    txq_raw = info["interface_txqueuelen"].get(iface)
    txq = colorize_txq(txq_raw)

    lnk = info["pcie"][iface]["lnksta"]
    width_raw = int(lnk["width"])
    max_width = int(lnk["max_width"])
    speed_raw = lnk["speed"]
    max_speed = lnk["max_speed"]

    width = colorize(width_raw, max_width)
    speed = colorize(speed_raw, max_speed)

    qc = info["queues"].get(iface)
    if isinstance(qc, dict):
        rx = colorize(qc["rx_cur"], qc["rx_max"])
        tx = colorize(qc["tx_cur"], qc["tx_max"])
        queues = f"RX {rx}, TX {tx}"
    else:
        queues = qc

    rb = info["rings"].get(iface, "not supported")

    # -----------------------------
    # ДИНАМИЧЕСКИЕ РЕКОМЕНДАЦИИ
    # -----------------------------
    rec = []

    if width_raw < max_width:
        rec.append(f"\\Z1PCIe работает на {width_raw} линиях, поддерживает {max_width}!\\Zn")

    if txq_raw is not None and txq_raw < 10000:
        rec.append("ip link set= {iface} 10000")
                    #      f"ip link set {iface} trtxqueuelen 10000\n"
    if not rec:
        rec.append("\\Z4Проблем не обнаружено\\Zn")

    rec_text = "\n".join(rec)

    # -----------------------------
    # ТЕКСТ ОКНА MAIN
    # -----------------------------
    text = (
        f"Интерфейс: \\Zb{iface}\\Zn\n"
        f"Driver: {drv}\n"
        f"Firmware: {fw}\n\n"
        f"TXQLEN: {txq}\n"
        f"PCIe Width: {width}\n"
        f"PCIe Speed: {speed}\n"
        f"Очереди: {queues}\n"
        f"Буферы: {rb}\n\n"
        "Рекомендации:\n"
        f"{rec_text}\n\n"
        "Выберите действие:\n"
        "  • Сохранить — записать команды тюнинга в файл\n"
        "  • Отмена — вернуться назад\n"
        "  • Дополнительно — открыть ethtool inspection\n"
    )

    code, btn = d.menu(
        text,
        choices=[
            ("save", "Сохранить"),
            ("ethtool", "Ethtool"),
            ("back", "Назад"),
        ],
        width=90,
        height=35
    )



    if code != d.OK:
        return

    if btn == "save":
        save_tuning_commands(d, iface, info)
        return show_interface_main(d, info, iface)

    elif btn == "ethtool":
        return show_ethtool_inspection(d, iface)

    elif btn == "back":
        return

def show_ethtool_inspection(d, iface):
    import subprocess

    i_out = subprocess.getoutput(f"ethtool -i {iface}")
    g_out = subprocess.getoutput(f"ethtool -g {iface}")
    l_out = subprocess.getoutput(f"ethtool -l {iface}")
    k_out = subprocess.getoutput(f"ethtool -k {iface}")

    text = (
        f"\\ZbEthtool inspection: {iface}\\Zn\n"
        "===============================\n\n"
        "\\Z4ethtool -i\\Zn\n"
        f"{i_out}\n\n"
        "\\Z4ethtool -g\\Zn\n"
        f"{g_out}\n\n"
        "\\Z4ethtool -l\\Zn\n"
        f"{l_out}\n"
        "\\Z4ethtool -k\\Zn\n"
        f"{k_out}\n"
    )

    d.msgbox(text, width=100, height=40)
def save_tuning_commands(d, iface, info):
    cmds = []

    txq = info["interface_txqueuelen"].get(iface)
    if txq is not None and txq < 10000:
        cmds.append(f"ip link set {iface} txqueuelen 10000")

    lnk = info["pcie"][iface]["lnksta"]
    width = int(lnk["width"])
    max_width = int(lnk["max_width"])
    if width < max_width:
        cmds.append(f"# ВНИМАНИЕ: {iface} работает на ширине {width}, максимум {max_width}")

    if not cmds:
        cmds.append("# Нет доступных команд тюнинга")

    cmd_text = "\n".join(cmds)

    code, path = d.inputbox(
        "Введите путь для сохранения файла:",
        init=f"/tmp/{iface}-tuning.sh",
        width=60
    )

    if code != d.OK:
        return

    try:
        with open(path, "w") as f:
            f.write(cmd_text)
        d.msgbox(f"Команды сохранены в {path}")
    except Exception as e:
        d.msgbox(f"Ошибка сохранения: {e}")

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
# 2.1 Настройка CPUF
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
from bras_autotune.irq import get_interface_irqs, get_irq_distribution, summarize_irq_distribution
# irq sub

def show_irq_distribution(d, iface):
    irqs = get_interface_irqs(iface)

    if not irqs:
        d.msgbox(f"Для интерфейса {iface} не найдено IRQ.", width=60)
        return

    dist = get_irq_distribution(irqs)
    summary = summarize_irq_distribution(dist)

    # Формируем красивый вывод
    text = f"IRQ распределение для интерфейса: {iface}\n"
    text += "=" * 60 + "\n\n"

    text += "IRQ → CPU распределение:\n\n"
    for irq, cpu_map in dist.items():
        text += f"IRQ {irq}:\n"
        for cpu, count in cpu_map.items():
            text += f"   CPU{cpu}: {count}\n"
        text += "\n"

    text += "\nСуммарная нагрузка по CPU:\n"
    text += "-" * 60 + "\n"

    for cpu, total in summary.items():
        text += f"CPU{cpu}: {total}\n"

    d.msgbox(text, width=90, height=40)

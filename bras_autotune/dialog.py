import os
from pathlib import Path
from bras_autotune.nic import list_physical_interfaces

import os
from pathlib import Path
from bras_autotune.nic import list_physical_interfaces

def interactive_select_ifaces_and_cores():
    print("=== BRAS AUTOTUNE ===")

    # Получаем физические интерфейсы
    phys = list_physical_interfaces()

    print("\nДоступные физические интерфейсы:")
    for i, iface in enumerate(phys):
        print(f"  {i}: {iface}")

    # Выбор WAN
    wan_idx = int(input("\nВыберите WAN интерфейс (номер): "))
    if_wan = phys[wan_idx]

    # Выбор BRAS
    bras_idx = int(input("Выберите LAN интерфейс (номер): "))
    if_bras = phys[bras_idx]

    # CPU
    total = os.cpu_count() or 1
    print(f"\nВсего CPU: {total}")

    data_cores = int(input("DATA-plane ядер: "))
    data_cpu_list = list(range(data_cores))
    ctrl_cpu_list = list(range(data_cores, total))

    # Выбор места сохранения
    print("\nКуда сохранить результат?")
    print("  1: Домашний каталог (~/bras-autotune)")
    print("  2: /tmp/bras-autotune")
    print("  3: /etc/network/interfaces.d/bras.conf (готовый конфиг)")

    save_choice = int(input("Выберите вариант: "))

    # Логика путей
    if save_choice == 1:
        out_dir = str(Path.home() / "bras-autotune")
        etc_mode = False

    elif save_choice == 2:
        out_dir = "/tmp/bras-autotune"
        etc_mode = False

    elif save_choice == 3:
        out_dir = "/etc/network/interfaces.d"
        etc_mode = True

    else:
        print("Неверный выбор, используем домашний каталог.")
        out_dir = str(Path.home() / "bras-autotune")
        etc_mode = False

    cfg = {
        "if_wan": if_wan,
        "if_bras": if_bras,
        "data_cores": data_cores,
        "data_cpu_list": data_cpu_list,
        "ctrl_cpu_list": ctrl_cpu_list,
        "data_mask_hex": format((1 << data_cores) - 1, "x"),
        "rxq_wan": 2,
        "rxq_bras": 2,
        "out_dir": out_dir,
        "etc_mode": etc_mode
    }

    if etc_mode:
        print("\nКонфиг будет сохранён в:")
        print("  /etc/network/interfaces.d/bras.conf")
        print("\nЧтобы применить конфигурацию:")
        print("  systemctl restart networking")
        print("или")
        print("  reboot")

    return cfg

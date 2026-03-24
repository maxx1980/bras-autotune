def fallback_mode():
    print("Fallback режим включён (TUI недоступен).")
    print("Введите параметры вручную.\n")

    cfg = {}

    cfg["if_wan"] = input("WAN интерфейс: ")
    cfg["if_bras"] = input("BRAS интерфейс: ")
    cfg["data_cores"] = int(input("Количество DATA-plane ядер: "))
    cfg["data_mask_hex"] = input("CPU mask (hex): ")
    cfg["rxq_wan"] = int(input("Очереди WAN: "))
    cfg["rxq_bras"] = int(input("Очереди BRAS: "))
    cfg["data_cpu_list"] = input("DATA CPU list: ")
    cfg["ctrl_cpu_list"] = input("CTRL CPU list: ")
    cfg["out_dir"] = input("Папка сохранения: ")
    cfg["etc_mode"] = False

    return cfg

def safe_int(value, default=0):
    """Безопасное преобразование в int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def generate_interface_recommendations(iface: str, stats: dict) -> list[str]:
    rec = []

    speed = stats.get("speed")
    pcie = stats.get("pcie_status", {})
    queues = stats.get("queues", {})
    rings = stats.get("ring_buffers", {})
    txqlen = stats.get("txq")
    health = stats.get("health", {})
    needs_tuning = stats.get("needs_tuning", False)

    # -----------------------------
    # 4. Health‑показатели
    # -----------------------------
    for key, value in health.items():
        if value == "NOT_SUPPORTED":
            if key == "buffers":
                rec.append(f"Ring buffers: unsupported.")
            elif key == "fw":
                rec.append(f"Прошивка: unknown.")
    #    
    #    elif value == "NOT_SUPPORTED":
    #        rec.append(f"Информация: {key} не поддерживается.")
    #    elif value == "OK":
    #        rec.append(f"Значение: {key} {value}.")

    # -----------------------------
    # -----------------------------
    # 1. PCIe рекомендации
    # -----------------------------
    cur_speed = pcie.get("speed")
    max_speed = pcie.get("max_speed")
    
    if cur_speed and max_speed and cur_speed != max_speed:
        rec.append(
            f"PCIe работает на {cur_speed}, хотя карта поддерживает {max_speed}. "
            f"Проверьте BIOS, ASPM и настройки PCIe power saving."
        )


    width = safe_int(pcie.get("width"))
    max_width = safe_int(pcie.get("max_width"))

    if width and max_width and width < max_width:
        rec.append(
            f"PCIe работает на x{width}, но карта поддерживает x{max_width}. "
            f"Возможна проблема со слотом или материнской платой."
        )
    txqlen = safe_int(stats.get("txqueuelen"))
    if txqlen < 10000:
        rec.append(
             f"TX {txqlen}очередь мала, нужно увеличить: [white]ip link set {iface} txqueuelen 10000[/white]"
        )    
    # -----------------------------
    # 2. Очереди RX/TX
    # -----------------------------
    rx_cur = safe_int(queues.get("rx_cur"))
    rx_max = safe_int(queues.get("rx_max"))
    tx_cur = safe_int(queues.get("tx_cur"))
    tx_max = safe_int(queues.get("tx_max"))

    if rx_cur < rx_max:
        rec.append(
            f"RX очередей: {rx_cur} из {rx_max}. "
            f"Рекомендуется включить все очереди ([white]ethtool -L[/white])."
        )

    if tx_cur < tx_max:
        rec.append(
            f"TX очередей: {tx_cur} из {tx_max}. "
            f"Рекомендуется включить все TX очереди."
        )

    # -----------------------------
    # 3. Ring buffers
    # -----------------------------
    rx_ring_cur = safe_int(rings.get("rx_cur"))
    rx_ring_max = safe_int(rings.get("rx_max"))
    tx_ring_cur = safe_int(rings.get("tx_cur"))
    tx_ring_max = safe_int(rings.get("tx_max"))
    if rx_ring_cur < rx_ring_max:
        rec.append(
            f"RX ring buffer: {rx_ring_cur} из {rx_ring_max}. "
            f"Увеличьте буфер: [white]ethtool -G {iface} rx {rx_ring_max}[/white]"
        )

    if tx_ring_cur < tx_ring_max:
        rec.append(
            f"TX ring buffer: {tx_ring_cur} из {tx_ring_max}. "
            f"Увеличьте TX буфер. [white]ethtool -G {iface} tx {tx_ring_max}[/white]"
        )



    # 5. needs_tuning
    # -----------------------------
    if needs_tuning and not rec:
        rec.append("Интерфейс требует тюнинга, но конкретные проблемы не обнаружены.")

    # -----------------------------
    # 6. Всё идеально
    # -----------------------------
    if not rec:
        rec.append("Интерфейс работает оптимально. Тюнинг не требуется.")

    return rec
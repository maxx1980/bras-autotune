def generate_recommendations(iface_stats: dict) -> list[str]:
    """
    Генерирует рекомендации по сетевому тюнингу на основе health-флагов,
    которые были сформированы в utils.get_all_interfaces_stats().

    Возвращает список строк.
    """

    rec = []
    health = iface_stats.get("health", {})

    # -----------------------------
    # Buffers
    # -----------------------------
    if health.get("buffers") == "NOT_OK":
        ring = iface_stats.get("ring_buffers", {})
        rx = ring.get("rx")
        tx = ring.get("tx")

        rec.append(
            f"Увеличить ring buffers: RX={rx}, TX={tx}. "
            "Рекомендуется минимум RX/TX >= 512."
        )

    # -----------------------------
    # PCIe
    # -----------------------------
    if health.get("pci") == "NOT_OK":
        pci = iface_stats.get("pci_addr")
        pcie = iface_stats.get("pcie_status")

        if pci is None:
            rec.append("Не удалось определить PCIe адрес интерфейса.")
        else:
            rec.append(
                f"Проблема с PCIe линком ({pci}). "
                "Проверьте скорость/ширину PCIe (lnksta)."
            )

    # -----------------------------
    # Firmware
    # -----------------------------
    if health.get("fw") == "NOT_OK":
        rec.append(
            "Прошивка NIC неизвестна или не определена. "
            "Рекомендуется обновить firmware до последней версии."
        )

    # -----------------------------
    # Driver
    # -----------------------------
    if health.get("driver") == "NOT_OK":
        rec.append(
            "Драйвер интерфейса не определён. "
            "Проверьте корректность модуля ядра или обновите драйвер."
        )

    # -----------------------------
    # Queues
    # -----------------------------
    if health.get("queues") == "NOT_OK":
        rec.append(
            "Не удалось определить RX/TX очереди. "
            "Проверьте поддержку очередей драйвером или ethtool."
        )
    # -----------------------------
    # PCIe SPEED (ширина линии)
    # -----------------------------
    if health.get("pcie_speed") == "NOT_OK":
        width = iface_stats["pcie_status"].get("width") if iface_stats.get("pcie_status") else None
        rec.append(
            f"Недостаточная ширина PCIe линии (width={width}). "
            "Для 10G NIC требуется минимум x4. Проверьте слот или переставьте карту."
        )

    # -----------------------------
    # PCIe GENERATION (скорость линии)
    # -----------------------------
    if health.get("pcie_generation") == "NOT_OK":
        speed = iface_stats["pcie_status"].get("speed") if iface_stats.get("pcie_status") else None
        rec.append(
            f"Низкая скорость PCIe (speed={speed}). "
            "Для 10G NIC требуется PCIe Gen3 (8GT/s). Проверьте BIOS/UEFI или слот."
        )

    # -----------------------------
    # Если всё хорошо
    # -----------------------------
    if not rec:
        rec.append("Проблем не обнаружено. Интерфейс настроен корректно.")

    return rec
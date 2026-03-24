import re
from collections import defaultdict


def get_interface_irqs(iface):
    """
    Возвращает список IRQ, связанных с сетевым интерфейсом.
    Читает /proc/interrupts и ищет строки с именем интерфейса.
    """
    irqs = []

    with open("/proc/interrupts") as f:
        for line in f:
            if iface in line:
                irq = line.split(":")[0].strip()
                if irq.isdigit():
                    irqs.append(int(irq))

    return irqs


def get_irq_distribution(irqs):
    """
    Возвращает распределение прерываний по CPU:
    {
        irq_number: {cpu_id: count, ...}
    }
    """
    dist = {}

    with open("/proc/interrupts") as f:
        lines = f.readlines()

    # первая строка содержит список CPU
    header = lines[0]
    cpu_count = len(header.split()) - 1  # CPU0 CPU1 CPU2 ...

    for line in lines[1:]:
        parts = line.split()
        irq = parts[0].replace(":", "")

        if not irq.isdigit():
            continue

        irq = int(irq)
        if irq not in irqs:
            continue

        # первые N колонок — это значения по CPU
        cpu_values = list(map(int, parts[1:1 + cpu_count]))

        dist[irq] = {cpu: cpu_values[cpu] for cpu in range(cpu_count)}

    return dist


def summarize_irq_distribution(dist):
    """
    Возвращает суммарную статистику:
    {
        cpu_id: total_interrupts
    }
    """
    summary = defaultdict(int)

    for irq, cpu_map in dist.items():
        for cpu, count in cpu_map.items():
            summary[cpu] += count

    return dict(summary)
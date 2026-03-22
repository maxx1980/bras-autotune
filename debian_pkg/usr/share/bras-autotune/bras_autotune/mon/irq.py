from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.reactive import reactive

import socket
import psutil
import re

from bras_autotune.mon.soft_net import SoftnetMonitor
from bras_autotune.utils import list_physical_interfaces   # ← ИСПРАВЛЕНО


# ------------------------------------------------------------
#  Utility functions
# ------------------------------------------------------------

def detect_active_iface():
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    for iface, st in stats.items():
        if iface == "lo":
            continue
        if iface.startswith("ppp"):
            continue
        if not st.isup:
            continue
        if iface not in addrs:
            continue

        has_ipv4 = any(a.family == socket.AF_INET for a in addrs[iface])
        if not has_ipv4:
            continue

        return iface

    return "lo"


def make_bar(value, max_value, width=30):
    if max_value <= 0:
        return "░" * width

    ratio = value / max_value
    ratio = max(0, min(1, ratio))

    filled = int(ratio * width)
    empty = width - filled

    return "█" * filled + "░" * empty


# ------------------------------------------------------------
#  IRQ-per-interface parsing
# ------------------------------------------------------------

def read_irq_line(irq):
    pattern = re.compile(rf"^\s*{irq}:")
    with open("/proc/interrupts") as f:
        for line in f:
            if pattern.match(line):
                return line
    return None


def get_irqs_for_iface(iface):
    irqs = []
    with open("/proc/interrupts") as f:
        for line in f:
            if f"{iface}-" in line:
                irq = line.split(":")[0].strip()
                if irq.isdigit():
                    irqs.append(int(irq))
    return irqs


def read_irq_counts(irq):
    line = read_irq_line(irq)
    if not line:
        return []

    parts = line.split()

    counts = []
    for p in parts[1:]:
        if p.isdigit():
            counts.append(int(p))
        else:
            break

    return counts


def read_irq_affinity(irq):
    try:
        with open(f"/proc/irq/{irq}/smp_affinity_list") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "-"


def read_irq_queue_name(irq):
    line = read_irq_line(irq)
    if not line:
        return "-"

    parts = line.split()
    parts = [p for p in parts if not p.endswith(":")]
    parts = [p for p in parts if not p.isdigit()]

    return parts[-1] if parts else "-"


class IrqInterfaceMonitor:
    def __init__(self, iface):
        self.iface = iface
        self.irqs = get_irqs_for_iface(iface)
        self.prev = {irq: read_irq_counts(irq) for irq in self.irqs}

    def update(self):
        rows = []
        for irq in self.irqs:
            now = read_irq_counts(irq)
            prev = self.prev.get(irq, [0] * len(now))

            diff = [n - p for n, p in zip(now, prev)]
            self.prev[irq] = now

            affinity = read_irq_affinity(irq)
            queue_name = read_irq_queue_name(irq)

            rows.append((irq, queue_name, affinity, diff))

        return rows


def format_irq_table(rows):
    if not rows:
        return "No IRQs for this interface"

    cpu_count = len(rows[0][3])

    header = (
        "IRQ   | QUEUE NAME           | AFFINITY | "
        + "  ".join([f"CPU{i:02d}" for i in range(cpu_count)])
        + "\n"
        + "-" * (30 + 7 * cpu_count)
    )

    lines = [header]

    for irq, queue_name, affinity, diff in rows:
        cpu_vals = "  ".join(f"{v:5d}" for v in diff)
        line = (
            f"{irq:4d} | "
            f"{queue_name:20s} | "
            f"{affinity:8s} | "
            f"{cpu_vals}"
        )
        lines.append(line)

    return "\n".join(lines)


# ------------------------------------------------------------
#  IrqMonitor UI
# ------------------------------------------------------------

class IrqMonitor(Vertical):

    can_focus = True

    def __init__(self, iface, history_len=60):
        super().__init__()
        self.iface = iface

        # ← ИСПРАВЛЕНО: список интерфейсов теперь из list_physical_interfaces()
        self.ifaces = list_physical_interfaces()

        self.iface_index = self.ifaces.index(iface) if iface in self.ifaces else 0

        self.iface_irq = IrqInterfaceMonitor(self.iface)
        self.softnet = SoftnetMonitor(history_len=history_len)

    def compose(self):
        yield Static(
            f"[b]IRQ Monitoring[/b]\n"
            f"Interface: [u]{self.iface}[/u]\n"
        )
        yield Static(
            f"[b]Space for switch next interface, ↑ back to menu[/b]\n"
        )

        yield Static("\n[u]IRQ per Interface[/u]")
        self.irq_iface_graph = Static("")
        yield self.irq_iface_graph

        yield Static("\n[u]Softnet Stat[/u]")
        self.softnet_graph = Static("")
        yield self.softnet_graph

    async def on_mount(self):
        self.focus()
        self.set_interval(1, self.update_all)

    def switch_iface(self):
        self.iface_index = (self.iface_index + 1) % len(self.ifaces)
        self.iface = self.ifaces[self.iface_index]

        self.iface_irq = IrqInterfaceMonitor(self.iface)

        self.children[0].update(
            f"[b]IRQ Monitoring[/b]\nInterface: [u]{self.iface}[/u]\n"
        )

        self.update_irq_interface()
        self.update_softnet()

    def update_all(self):
        self.update_irq_interface()
        self.update_softnet()

    def update_irq_interface(self):
        rows = self.iface_irq.update()
        table = format_irq_table(rows)
        self.irq_iface_graph.update(table)

    def update_softnet(self):
        diffs = self.softnet.update()
        max_total = self.softnet.max_history("total")

        header = (
            "CPU                      | TOTAL | DROP | SQ | COL | RPS\n"
            "---------------------------------------------------------"
        )

        lines = [header]

        for d in diffs:
            bar = make_bar(d.total, max_total, width=20)
            line = (
                f"CPU{d.cpu:02d} {bar} "
                f"{d.total:6d} "
                f"{d.dropped:5d} "
                f"{d.time_squeeze:4d} "
                f"{d.cpu_collision:4d} "
                f"{d.received_rps:4d}"
            )
            lines.append(line)

        self.softnet_graph.update("\n".join(lines))
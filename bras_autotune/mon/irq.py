from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.reactive import reactive
import socket
from collections import defaultdict, deque
import psutil

#from bras_autotune.mon.utils import make_bar
from bras_autotune.mon.soft_net import SoftnetMonitor
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

        # есть IPv4?
        has_ipv4 = any(a.family == socket.AF_INET for a in addrs[iface])
        if not has_ipv4:
            continue

        return iface

    return "lo"  # fallback
def make_bar(value, max_value, width=30):
    """Рисует текстовый бар-график фиксированной ширины."""
    if max_value <= 0:
        return "░" * width

    ratio = value / max_value
    if ratio < 0:
        ratio = 0
    if ratio > 1:
        ratio = 1

    filled = int(ratio * width)
    empty = width - filled

    return "█" * filled + "░" * empty

def read_softirq_per_cpu():
    """Возвращает softirq по ядрам (сумма всех типов)."""
    with open("/proc/softirqs") as f:
        lines = f.readlines()

    cpu_count = len(lines[0].split()) - 1
    totals = [0] * cpu_count

    for line in lines[1:]:
        parts = line.split()
        if len(parts) < cpu_count + 1:
            continue
        for i in range(cpu_count):
            totals[i] += int(parts[i + 1])

    return totals

def read_irq_per_cpu():
    """Возвращает IRQ по CPU (сумма всех IRQ)."""
    with open("/proc/interrupts") as f:
        lines = f.readlines()

    cpu_count = len(lines[0].split()) - 1
    totals = [0] * cpu_count

    for line in lines[1:]:
        parts = line.split()
        if len(parts) < cpu_count + 1:
            continue
        for i in range(cpu_count):
            try:
                totals[i] += int(parts[i + 1])
            except ValueError:
                pass

    return totals

# -----------------------------
# Irq View
# -----------------------------
class IrqView(Vertical):
    prev = reactive([])

    def __init__(self):
        super().__init__()
        self.update_interval = 1

    def compose(self) -> ComposeResult:
        yield Static("[bold]Live SoftIRQ Monitoring[/bold]\n")

class IrqMonitor(Vertical):
    """
    Экран мониторинга IRQ + SoftIRQ + SoftnetStat.
    """
    def __init__(self, iface, history_len=60):
        super().__init__()
        self.iface = iface

        # softnet монитор
        self.softnet = SoftnetMonitor(history_len=history_len)

    def compose(self):
        yield Static(
            f"[b]IRQ Monitoring[/b]\n"
            f"Interface: [u]{self.iface}[/u]\n"
        )

 

        # SoftnetStat
        yield Static("\n[u]Softnet Stat[/u]")
        self.softnet_graph = Static("")
        yield self.softnet_graph


        self.set_interval(1, self.update_all)

    def update_all(self):
        self.update_softnet()

    # ---------------- IRQ ----------------
 

    # ---------------- SoftIRQ ----------------

    # ---------------- SoftnetStat ----------------
    def update_softnet(self):
        diffs = self.softnet.update()
        max_total = self.softnet.max_history("total")

        # Заголовок таблицы
        header = (
            "CPU   |                         TOTAL | DROP | SQ | COL | RPS\n"
            "________________________________________________________________"
        )

        lines = [header]

        for d in diffs:
            bar = make_bar(d.total, max_total, width=20)

            line = (
                f"CPU{d.cpu:02d} {bar} "
                f"{d.total:9d} "
                f"{d.dropped:6d} "
                f"{d.time_squeeze:5d} "
                f"{d.cpu_collision:4d} "
                f"{d.received_rps:4d}"
            )

            lines.append(line)

        self.softnet_graph.update("\n".join(lines))

from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual.app import ComposeResult
from textual.reactive import reactive
import psutil
import os
import socket

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

# масштабирование графиков
def make_bar(value, max_value, width=30):
    if max_value <= 0:
        return "░" * width
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)



# -----------------------------
# IRQ
# -----------------------------
def read_irq_per_cpu():
    cpu_count = psutil.cpu_count(logical=True)
    totals = [0] * cpu_count

    with open("/proc/interrupts") as f:
        lines = f.readlines()

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
# SoftIRQ
# -----------------------------
def read_softirq_per_cpu():
    cpu_count = psutil.cpu_count(logical=True)
    totals = [0] * cpu_count

    with open("/proc/softirqs") as f:
        lines = f.readlines()

    for line in lines[1:]:
        parts = line.split()
        if len(parts) < cpu_count + 1:
            continue
        for i in range(cpu_count):
            totals[i] += int(parts[i + 1])

    return totals


# -----------------------------
# RPS activity (softnet_stat)
# -----------------------------
def read_rps_activity():
    with open("/proc/net/softnet_stat") as f:
        lines = f.readlines()

    values = []
    for line in lines:
        parts = line.split()
        processed = int(parts[0], 16)
        values.append(processed)

    return values






# -----------------------------
# Live View
# -----------------------------
class LiveCPUView(Vertical):
    cpu_data = reactive([])
    irq_prev = reactive([])
    soft_prev = reactive([])
    rps_prev = reactive([])

    def __init__(self):
        super().__init__()
        self.update_interval = 1
        self.iface = detect_active_iface()
        from collections import defaultdict, deque
        self.history_irq = defaultdict(lambda: deque(maxlen=60))
        self.history_soft = defaultdict(lambda: deque(maxlen=60))
        self.history_rps = defaultdict(lambda: deque(maxlen=60))


    def compose(self) -> ComposeResult:
        yield Static("[bold]Live Monitoring[/bold]\n"
                     "[b]↑ back to menu[/b]\n"
                    )

        with Horizontal():

            # ---------------- LEFT COLUMN ----------------
            with Vertical(id="left-col"):

                yield Static("[u]CPU Load[/u]")
                self.cpu_graph = Static("")
                yield self.cpu_graph

                yield Static("\n[u]IRQ per CPU[/u]")
                self.irq_graph = Static("")
                yield self.irq_graph


                


            # ---------------- RIGHT COLUMN ----------------
            with Vertical(id="right-col"):
                self.iface_label = Static(f"[u]Interface:[/u] {self.iface}")
                yield self.iface_label
                yield Static("\n[u]RPS Activity (softnet_stat)[/u]")
                self.rps_graph = Static("")
                yield self.rps_graph

                yield Static("\n[u]SoftIRQ per CPU[/u]")
                self.soft_graph = Static("")
                yield self.soft_graph



    async def on_mount(self):
        self.irq_prev = read_irq_per_cpu()
        self.soft_prev = read_softirq_per_cpu()
        self.rps_prev = read_rps_activity()
        self.set_interval(self.update_interval, self.update_all)

    def update_all(self):
        self.update_cpu()
        self.update_irq()
        self.update_softirq()
        self.update_rps()

    # ---------------- CPU ----------------
    def update_cpu(self):
        usage = psutil.cpu_percent(percpu=True)
        lines = []
        for i, val in enumerate(usage):
            bar = "█" * int(val / 5) + "░" * (20 - int(val / 5))
            lines.append(f"core{i:02d}: {bar} {val:5.1f}%")
        self.cpu_graph.update("\n".join(lines))

    # ---------------- IRQ ----------------
    def update_irq(self):
        now = read_irq_per_cpu()
        diff = [now[i] - self.irq_prev[i] for i in range(len(now))]
        self.irq_prev = now

        # обновляем историю
        for cpu, val in enumerate(diff):
            self.history_irq[cpu].append(val)

        # максимум по истории
        max_irq = max((max(v) for v in self.history_irq.values() if len(v)), default=1)

        lines = []
        for cpu, val in enumerate(diff):
            bar = make_bar(val, max_irq, width=30)
            lines.append(f"CPU{cpu:02d}: {bar} {val}")
        self.irq_graph.update("\n".join(lines))


    # ---------------- SoftIRQ ----------------
    def update_softirq(self):   
        now = read_softirq_per_cpu()
        diff = [now[i] - self.soft_prev[i] for i in range(len(now))]
        self.soft_prev = now

        for cpu, val in enumerate(diff):
            self.history_soft[cpu].append(val)

        max_soft = max((max(v) for v in self.history_soft.values() if len(v)), default=1)

        lines = []
        for cpu, val in enumerate(diff):
            bar = make_bar(val, max_soft, width=30)
            lines.append(f"CPU{cpu:02d}: {bar} {val}")
        self.soft_graph.update("\n".join(lines))



    # ---------------- RPS activity ----------------
    def update_rps(self):
        now = read_rps_activity()
        diff = [now[i] - self.rps_prev[i] for i in range(len(now))]
        self.rps_prev = now

        for cpu, val in enumerate(diff):
            self.history_rps[cpu].append(val)

        max_rps = max((max(v) for v in self.history_rps.values() if len(v)), default=1)

        lines = []
        for cpu, val in enumerate(diff):
            bar = make_bar(val, max_rps, width=30)
            lines.append(f"CPU{cpu:02d}: {bar} {val} pkts/s")
        self.rps_graph.update("\n".join(lines))


    # ---------------- Ring buffers ----------------
    def update_ring(self):
        rx, tx = read_ring_usage(self.iface)

        lines = ["[RX]"]
        for q, pending, maxp in rx:
            bar = "█" * int((pending / maxp) * 20) + "░" * (20 - int((pending / maxp) * 20))
            lines.append(f"{q}: {bar} {pending}/{maxp}")

        lines.append("\n[TX]")
        for q, pending, maxp in tx:
            bar = "█" * int((pending / maxp) * 20) + "░" * (20 - int((pending / maxp) * 20))
            lines.append(f"{q}: {bar} {pending}/{maxp}")

        self.ring_graph.update("\n".join(lines))
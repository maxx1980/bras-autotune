from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual.app import ComposeResult
from textual.reactive import reactive
import psutil
import os



# -----------------------------
# IRQ
# -----------------------------
def read_irq_per_cpu():
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
# SoftIRQ
# -----------------------------
def read_softirq_per_cpu():
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
# ksoftirqd load
# -----------------------------
def read_ksoftirqd_load():
    loads = []
    for cpu in range(psutil.cpu_count()):
        name = f"ksoftirqd/{cpu}"
        cpu_load = 0
        for p in psutil.process_iter(["name", "cpu_percent"]):
            if p.info["name"] == name:
                cpu_load = p.info["cpu_percent"]
                break
        loads.append(cpu_load)
    return loads


# -----------------------------
# kworker load
# -----------------------------
def read_kworker_load():
    loads = {}
    for p in psutil.process_iter(["name", "cpu_percent"]):
        name = p.info["name"]
        if name.startswith("kworker/"):
            loads[name] = p.info["cpu_percent"]
    return loads



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
        self.iface = "eth0"

    def compose(self) -> ComposeResult:
        yield Static("[bold]Live Monitoring[/bold]\n")

        with Horizontal():

            # ---------------- LEFT COLUMN ----------------
            with Vertical(id="left-col"):

                yield Static("[u]CPU Load[/u]")
                self.cpu_graph = Static("")
                yield self.cpu_graph

                yield Static("\n[u]IRQ per CPU[/u]")
                self.irq_graph = Static("")
                yield self.irq_graph

                yield Static("\n[u]SoftIRQ per CPU[/u]")
                self.soft_graph = Static("")
                yield self.soft_graph
                
                yield Static("\n[u]RPS Activity (softnet_stat)[/u]")
                self.rps_graph = Static("")
                yield self.rps_graph

            # ---------------- RIGHT COLUMN ----------------
            with Vertical(id="right-col"):

                yield Static("[u]ksoftirqd Load[/u]")
                self.ksoft_graph = Static("")
                yield self.ksoft_graph

                yield Static("\n[u]kworker Load[/u]")
                self.kworker_graph = Static("")
                yield self.kworker_graph




    async def on_mount(self):
        self.irq_prev = read_irq_per_cpu()
        self.soft_prev = read_softirq_per_cpu()
        self.rps_prev = read_rps_activity()
        self.set_interval(self.update_interval, self.update_all)

    def update_all(self):
        self.update_cpu()
        self.update_irq()
        self.update_softirq()
        self.update_ksoftirqd()
        self.update_kworker()
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

        lines = []
        for i, val in enumerate(diff):
            bar = "█" * min(20, val // 50) + "░" * (20 - min(20, val // 50))
            lines.append(f"CPU{i:02d}: {bar} {val}")
        self.irq_graph.update("\n".join(lines))

    # ---------------- SoftIRQ ----------------
    def update_softirq(self):
        now = read_softirq_per_cpu()
        diff = [now[i] - self.soft_prev[i] for i in range(len(now))]
        self.soft_prev = now

        lines = []
        for i, val in enumerate(diff):
            bar = "█" * min(20, val // 50) + "░" * (20 - min(20, val // 50))
            lines.append(f"CPU{i:02d}: {bar} {val}")
        self.soft_graph.update("\n".join(lines))

    # ---------------- ksoftirqd ----------------
    def update_ksoftirqd(self):
        loads = read_ksoftirqd_load()
        lines = []
        for i, val in enumerate(loads):
            bar = "█" * int(val / 5) + "░" * (20 - int(val / 5))
            lines.append(f"ksoftirqd/{i}: {bar} {val:5.1f}%")
        self.ksoft_graph.update("\n".join(lines))

    # ---------------- kworker ----------------
    def update_kworker(self):
        loads = read_kworker_load()
        lines = []
        for name, val in loads.items():
            bar = "█" * int(val / 5) + "░" * (20 - int(val / 5))
            lines.append(f"{name}: {bar} {val:5.1f}%")
        self.kworker_graph.update("\n".join(lines))

    # ---------------- RPS activity ----------------
    def update_rps(self):
        now = read_rps_activity()
        diff = [now[i] - self.rps_prev[i] for i in range(len(now))]
        self.rps_prev = now

        lines = []
        for i, val in enumerate(diff):
            bar = "█" * min(20, val // 100) + "░" * (20 - min(20, val // 100))
            lines.append(f"CPU{i:02d}: {bar} {val} pkts/s")
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
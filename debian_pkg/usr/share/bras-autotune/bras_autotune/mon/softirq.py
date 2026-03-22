from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.reactive import reactive


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


class LiveSoftIRQView(Vertical):
    prev = reactive([])

    def __init__(self):
        super().__init__()
        self.update_interval = 1

    def compose(self) -> ComposeResult:
        yield Static("[bold]Live SoftIRQ Monitoring[/bold]\n")
        self.graph = Static("", id="softirq-graph")
        yield self.graph

    async def on_mount(self):
        self.prev = read_softirq_per_cpu()
        self.set_interval(self.update_interval, self.update_softirq)

    def update_softirq(self):
        now = read_softirq_per_cpu()
        diff = [now[i] - self.prev[i] for i in range(len(now))]
        self.prev = now
        self.render_graph(diff)

    def render_graph(self, values):
        lines = []
        for i, val in enumerate(values):
            bar_len = min(20, val // 50)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"CPU{i:02d}: {bar} {val}")
        self.graph.update("\n".join(lines))
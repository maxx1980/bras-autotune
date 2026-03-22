from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.reactive import reactive
import asyncio


def read_irq_per_cpu():
    """Возвращает список IRQ по каждому CPU."""
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


class LiveIRQView(Vertical):
    irq_prev = reactive([])

    def __init__(self):
        super().__init__()
        self.update_interval = 1

    def compose(self) -> ComposeResult:
        yield Static("[bold]Live IRQ Monitoring[/bold]\n")
        self.graph = Static("", id="irq-graph")
        yield self.graph

    async def on_mount(self):
        self.irq_prev = read_irq_per_cpu()
        self.set_interval(self.update_interval, self.update_irq)

    def update_irq(self):
        now = read_irq_per_cpu()
        diff = [now[i] - self.irq_prev[i] for i in range(len(now))]
        self.irq_prev = now
        self.render_graph(diff)

    def render_graph(self, values):
        lines = []
        for i, val in enumerate(values):
            bar_len = min(20, val // 50)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"CPU{i:02d}: {bar} {val}")
        self.graph.update("\n".join(lines))
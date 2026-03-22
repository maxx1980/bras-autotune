from textual.screen import Screen
from textual.widgets import Static

class IRQScreen(Screen):

    def compose(self):
        yield Static("IRQ List", id="title")
        yield Static(self._scan(), id="irq")

    def _scan(self):
        out = []
        with open("/proc/interrupts") as f:
            for line in f:
                out.append(line.rstrip())
        return "\n".join(out)

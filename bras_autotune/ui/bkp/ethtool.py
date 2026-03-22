from textual.screen import Screen
from textual.widgets import Static
import subprocess

class EthtoolScreen(Screen):

    def __init__(self, iface="eth0"):
        super().__init__()
        self.iface = iface

    def compose(self):
        yield Static(f"Ethtool: {self.iface}", id="title")
        yield Static(self._run(), id="ethtool")

    def _run(self):
        try:
            out = subprocess.check_output(["ethtool", self.iface], text=True)
            return out
        except:
            return "ethtool not available"

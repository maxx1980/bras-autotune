from textual.screen import Screen
from textual.widgets import Static
import os

class PCIEScreen(Screen):

    def compose(self):
        yield Static("PCIe Devices", id="title")
        yield Static(self._scan(), id="pcie")

    def _scan(self):
        out = []
        for dev in os.listdir("/sys/bus/pci/devices"):
            path = f"/sys/bus/pci/devices/{dev}"
            vendor = self._read(path + "/vendor")
            device = self._read(path + "/device")
            out.append(f"{dev}: vendor={vendor}, device={device}")
        return "\n".join(out)

    def _read(self, path):
        try:
            with open(path) as f:
                return f.read().strip()
        except:
            return "N/A"

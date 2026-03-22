from textual.screen import Screen
from textual.widgets import Static
import os

class InterfaceViewScreen(Screen):

    def __init__(self, iface="eth0"):
        super().__init__()
        self.iface = iface

    def compose(self):
        yield Static(f"Interface: {self.iface}", id="title")
        yield Static(self._info(), id="info")

    def _info(self):
        base = f"/sys/class/net/{self.iface}"
        data = []

        def read(path):
            try:
                with open(path) as f:
                    return f.read().strip()
            except:
                return "N/A"

        data.append(f"State: {read(base + '/operstate')}")
        data.append(f"Speed: {read(base + '/speed')}")
        data.append(f"MTU: {read(base + '/mtu')}")
        data.append(f"MAC: {read(base + '/address')}")

        return "\n".join(data)

from textual.screen import Screen
from textual.widgets import Static, DataTable
import os

class InterfacesScreen(Screen):

    def compose(self):
        yield Static("Network Interfaces", id="title")
        table = DataTable(id="ifaces")
        table.add_columns("Name", "Driver", "PCI", "State")
        for iface in os.listdir("/sys/class/net"):
            driver = self._get_driver(iface)
            pci = self._get_pci(iface)
            state = self._get_state(iface)
            table.add_row(iface, driver, pci, state)
        yield table

    def _get_driver(self, iface):
        path = f"/sys/class/net/{iface}/device/driver/module"
        if os.path.islink(path):
            return os.path.basename(os.readlink(path))
        return "unknown"

    def _get_pci(self, iface):
        path = f"/sys/class/net/{iface}/device"
        if os.path.islink(path):
            return os.path.basename(os.readlink(path))
        return "-"

    def _get_state(self, iface):
        try:
            with open(f"/sys/class/net/{iface}/operstate") as f:
                return f.read().strip()
        except:
            return "unknown"

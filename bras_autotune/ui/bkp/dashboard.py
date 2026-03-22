from textual.app import App
from textual.widgets import Static
from textual.screen import Screen
from textual.reactive import reactive
from pathlib import Path

from bras_autotune.ui.menu import MenuBar
from bras_autotune.utils import get_all_interfaces_stats


# ============================================================
# 2. Экран списка интерфейсов
# ============================================================
class InterfacesScreen(Screen):

    selected = reactive(0)

    def __init__(self, interfaces_stats):
        super().__init__()
        self.stats = interfaces_stats
        self.ifaces = list(interfaces_stats.keys())

    def compose(self):
        yield Static("Interfaces:", id="title")

        for iface in self.ifaces:
            item = Static(f"  {iface}", classes="iface-item")
            item.can_focus = True
            yield item

    def on_mount(self):
        self.highlight()
        self.focus()

    def highlight(self):
        items = self.query(".iface-item")
        for i, widget in enumerate(items):
            if i == self.selected:
                widget.update(f"> {self.ifaces[i]}")
                widget.add_class("selected")
            else:
                widget.update(f"  {self.ifaces[i]}")
                widget.remove_class("selected")

    def on_key(self, event):
        if event.key == "up":
            self.selected = max(0, self.selected - 1)
            self.highlight()

        elif event.key == "down":
            self.selected = min(len(self.ifaces) - 1, self.selected + 1)
            self.highlight()

        elif event.key == "enter":
            iface = self.ifaces[self.selected]
            self.app.push_screen(InterfaceDetailsScreen(iface, self.stats[iface]))


# ============================================================
# 3. Экран интерфейса
# ============================================================
class InterfaceDetailsScreen(Screen):

    def __init__(self, iface, stats):
        super().__init__()
        self.iface = iface
        self.stats = stats

    def compose(self):
        yield Static(f"Interface: {self.iface}", id="title")

        for key, value in self.stats.items():
            yield Static(f"{key}: {value}")

    def on_key(self, event):
        if event.key == "escape":
            self.app.pop_screen()


# ============================================================
# 4. Главный экран
# ============================================================
class DashboardScreen(Screen):

    def compose(self):
        yield MenuBar(id="menu")
        yield Static("Welcome to Network Dashboard", id="content")

    def on_mount(self):
        self.query_one(MenuBar).focus()

    def on_key(self, event):
        if event.key in ("left", "right", "up", "down"):
            return


# ============================================================
# 5. Приложение
# ============================================================
class DashboardApp(App):

    CSS_PATH = Path(__file__).with_suffix(".css")

    def on_mount(self):
        self.push_screen(DashboardScreen())

    def on_key(self, event):
        pass


if __name__ == "__main__":
    DashboardApp().run()
from textual.app import App
from textual.widgets import Static
from textual.containers import Vertical
from textual.screen import Screen
from textual.reactive import reactive
from pathlib import Path

from bras_autotune.utils import get_all_interfaces_stats


# ============================================================
# 1. Верхнее меню (как в MC)
# ============================================================
MENU_ITEMS = {
    "Interfaces": ["Show interfaces", "PCIe", "IRQ", "Ethtool"],
    "CPU": ["Governor", "Affinity"],
    "System": ["Dmesg", "Sysctl"],
    "Help": ["About"],
    "Exit": ["Quit"],
}
class DropdownMenu(Static):
    can_focus = True

    def __init__(self, items, parent_menu):
        super().__init__()
        self.items = items
        self.parent_menu = parent_menu
        self.selected = 0

    def compose(self):
        for item in self.items:
            yield Static(item, classes="dropdown-item")

    def on_mount(self):
        self.highlight()
        self.focus()

    def highlight(self):
        widgets = self.query(".dropdown-item")
        for i, w in enumerate(widgets):
            if i == self.selected:
                w.update(f"> {self.items[i]}")
                w.add_class("selected")
            else:
                w.update(f"  {self.items[i]}")
                w.remove_class("selected")

    def on_key(self, event):
        key = event.key

        if key == "down":
            self.selected = min(self.selected + 1, len(self.items) - 1)
            self.highlight()

        elif key == "up":
            if self.selected == 0:
                self.parent_menu.close_dropdown()
            else:
                self.selected -= 1
                self.highlight()

        elif key == "enter":
            self.parent_menu.activate_dropdown_item(self.items[self.selected])

        elif key == "escape":
            self.parent_menu.close_dropdown()

class MenuBar(Static):
    can_focus = True

    items = list(MENU_ITEMS.keys())
    selected = reactive(0)
    active = reactive(True)
    dropdown = None

    def compose(self):
        self.label = Static(self.render_menu(), id="menubar")
        yield self.label

    def render_menu(self):
        parts = []
        for i, item in enumerate(self.items):
            if self.active and i == self.selected:
                parts.append(f"[reverse]{item}[/reverse]")
            else:
                parts.append(item)
        return " | ".join(parts)

    def activate_menu(self):
        if not self.active:
            self.active = True
            self.selected = 0
            self.label.update(self.render_menu())
            self.focus()

    def open_dropdown(self):
        if self.dropdown:
            self.dropdown.remove()

        submenu = MENU_ITEMS[self.items[self.selected]]
        self.dropdown = DropdownMenu(submenu, self)
        self.mount(self.dropdown)

    def close_dropdown(self):
        if self.dropdown:
            self.dropdown.remove()
            self.dropdown = None
        self.focus()

    def activate_dropdown_item(self, item):
        # Здесь вызываем нужный экран
        if item == "Show interfaces":
            stats = get_all_interfaces_stats()
            self.app.push_screen(InterfacesScreen(stats))

        elif item == "Quit":
            self.app.exit()

        self.close_dropdown()

    def on_key(self, event):
        key = event.key

        if key in ("left", "right", "down"):
            self.activate_menu()

        if not self.active:
            return

        if key == "left":
            self.selected = (self.selected - 1) % len(self.items)
            self.label.update(self.render_menu())

        elif key == "right":
            self.selected = (self.selected + 1) % len(self.items)
            self.label.update(self.render_menu())

        elif key == "down":
            self.open_dropdown()

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

    # -----------------------------
    # Подсветка выбранного пункта
    # -----------------------------
    def highlight(self):
        items = self.query(".iface-item")
        for i, widget in enumerate(items):
            if i == self.selected:
                widget.update(f"> {self.ifaces[i]}")
                widget.add_class("selected")
            else:
                widget.update(f"  {self.ifaces[i]}")
                widget.remove_class("selected")

    # -----------------------------
    # Навигация ↑ ↓ Enter
    # -----------------------------
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

    # -----------------------------
    # Клик мышкой
    # -----------------------------
    def on_click(self, event):
        widget = event.target
        if "iface-item" in widget.classes:
            iface = widget.renderable.strip("> ").strip()
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
        # Блокируем стрелки, чтобы они не шли дальше
        if event.key in ("left", "right", "up", "down"):
            return

# ============================================================
# 5. Приложение
# ============================================================
class DashboardApp(App):

    CSS_PATH = Path(__file__).with_suffix(".css")

    def on_mount(self):
        self.push_screen(DashboardScreen())

    # Убираем обработку стрелок — она ломает меню
    def on_key(self, event):
        pass


if __name__ == "__main__":
    DashboardApp().run()
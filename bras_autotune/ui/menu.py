from textual.widgets import Static
from textual.reactive import reactive

from bras_autotune.utils import get_all_interfaces_stats


# ============================================================
# Структура меню
# ============================================================
MENU_ITEMS = {
    "Interfaces": ["Show interfaces", "PCIe", "IRQ", "Ethtool"],
    "CPU": ["Governor", "Affinity"],
    "System": ["Dmesg", "Sysctl"],
    "Help": ["About"],
    "Exit": ["Quit"],
}


# ============================================================
# Выпадающее меню (MC‑стиль)
# ============================================================
class DropdownMenu(Static):
    can_focus = True

    def __init__(self, items, parent_menu):
        super().__init__(classes="dropdown-menu")
        self.items = items
        self.parent_menu = parent_menu
        self.selected = 0

        self.menu_width = max(len(i) for i in items) + 4

    def compose(self):
        for item in self.items:
            yield Static(
                f"  {item.ljust(self.menu_width - 2)}",
                classes="dropdown-item"
            )

    def on_mount(self):
        self.highlight()
        self.focus()

    def highlight(self):
        widgets = self.query(".dropdown-item")
        for i, w in enumerate(widgets):
            if i == self.selected:
                w.update(f"> {self.items[i].ljust(self.menu_width - 2)}")
                w.add_class("selected")
            else:
                w.update(f"  {self.items[i].ljust(self.menu_width - 2)}")
                w.remove_class("selected")


# ============================================================
# Верхнее меню
# ============================================================
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

        # позиционируем подменю под выбранным пунктом
        self.dropdown.styles.margin = (1, 0, 0, self.selected * 12)

        self.mount(self.dropdown)

    def close_dropdown(self):
        if self.dropdown:
            self.dropdown.remove()
            self.dropdown = None
        self.focus()

    def activate_dropdown_item(self, item):
        if item == "Show interfaces":
            stats = get_all_interfaces_stats()
            from bras_autotune.ui.dashboard import InterfacesScreen
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
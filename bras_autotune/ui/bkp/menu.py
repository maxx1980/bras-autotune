from textual.widgets import Static
from textual.reactive import reactive

from bras_autotune.utils import get_all_interfaces_stats, list_physical_interfaces


# ============================================================
# Структура меню
# ============================================================
MENU_ITEMS = {
    "Interfaces": ["__interfaces__", "PCIe", "IRQ", "Ethtool"],
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

        # ширина текста (для выравнивания стрелки)
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


# ============================================================
# Верхнее меню
# ============================================================
class MenuBar(Static):
    can_focus = True

    items = list(MENU_ITEMS.keys())
    selected = reactive(0)
    dropdown = None

    def compose(self):
        self.label = Static(self.render_menu(), id="menubar")
        yield self.label

    def render_menu(self):
        parts = []
        for i, item in enumerate(self.items):
            if i == self.selected:
                parts.append(f"[reverse]{item}[/reverse]")
            else:
                parts.append(item)
        return " | ".join(parts)

    def open_dropdown(self):
        if self.dropdown:
            self.dropdown.remove()

        submenu = MENU_ITEMS[self.items[self.selected]]

        # динамическое подменю интерфейсов
        if "__interfaces__" in submenu:
            interfaces = list_physical_interfaces()
            submenu = interfaces + [item for item in submenu if item != "__interfaces__"]

        self.dropdown = DropdownMenu(submenu, self)

        # позиционируем подменю под выбранным пунктом
        self.dropdown.styles.margin = (1, 0, 0, self.selected * 12)

        self.mount(self.dropdown)
        self.dropdown.focus()

    def close_dropdown(self):
        if self.dropdown:
            self.dropdown.remove()
            self.dropdown = None
        self.focus()

    def activate_dropdown_item(self, item):

        # если выбрали интерфейс
        if item in list_physical_interfaces():
            stats = get_all_interfaces_stats()
            from bras_autotune.ui.dashboard import InterfacesScreen
            self.app.push_screen(InterfacesScreen(stats))
            self.close_dropdown()
            return

        if item == "Quit":
            self.app.exit()

        self.close_dropdown()

    def on_key(self, event):

        # если открыто подменю — не трогаем клавиши
        if self.dropdown:
            return

        key = event.key

        # стрелки влево/вправо — переключают пункты меню
        if key == "left":
            self.selected = (self.selected - 1) % len(self.items)
            self.label.update(self.render_menu())
            return

        if key == "right":
            self.selected = (self.selected + 1) % len(self.items)
            self.label.update(self.render_menu())
            return

        # Enter — открыть подменю
        if key == "enter":
            self.open_dropdown()
            return
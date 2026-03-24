from textual.widgets import Static
from textual.reactive import reactive

from bras_autotune.utils import get_all_interfaces_stats, list_physical_interfaces
from bras_autotune.ui.screens import InterfacesView


MENU_ITEMS = {
    "Interfaces": ["__interfaces__"],
    "Monitoring": ["Live", "Irq monitoring"],
    "System": ["Dmesg", "Sysctl"],
    "Tools": ["Wizard"],
    "Help": ["Tuning", "About"],
    "Exit": ["Quit"],
}


# ============================================================
# DROPDOWN MENU
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

    def on_key(self, event):
        key = event.key

        if key == "down":
            self.selected = min(self.selected + 1, len(self.items) - 1)
            self.highlight()
            event.stop()
            return

        elif key == "up":
            if self.selected == 0:
                self.parent_menu.close_dropdown()
            else:
                self.selected -= 1
                self.highlight()
            event.stop()
            return

        elif key == "enter":
            self.parent_menu.activate_dropdown_item(self.items[self.selected])
            event.stop()
            return

        elif key == "escape":
            self.parent_menu.close_dropdown()
            event.stop()
            return


# ============================================================
# TOP MENU BAR
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

    # --------------------------------------------------------
    # DROPDOWN CONTROL
    # --------------------------------------------------------

    def open_dropdown(self):
        if self.dropdown:
            self.dropdown.remove()

        submenu = MENU_ITEMS[self.items[self.selected]]

        # Expand __interfaces__
        if "__interfaces__" in submenu:
            interfaces = list_physical_interfaces()
            submenu = interfaces + [i for i in submenu if i != "__interfaces__"]

        self.dropdown = DropdownMenu(submenu, self)
        self.dropdown.styles.margin = (1, 0, 0, self.selected * 12)

        self.mount(self.dropdown)
        self.dropdown.focus()

    def close_dropdown(self):
        if self.dropdown:
            self.dropdown.remove()
            self.dropdown = None
        self.focus()

    # --------------------------------------------------------
    # ACTIVATE MENU ITEM
    # --------------------------------------------------------

    def activate_dropdown_item(self, item):

        interfaces = list_physical_interfaces()

        if item in interfaces:
            stats = get_all_interfaces_stats()
            self.app.screen.show_interface_details(item, stats[item])
            self.close_dropdown()
            return

        if item == "Live":
            self.app.screen.show_live_monitoring()
            self.close_dropdown()
            return

        if item == "Irq monitoring":
            self.app.screen.show_irq_monitoring()
            self.close_dropdown()
            return
        if item == "Tuning":
            self.app.screen.show_help_tuning()
            self.close_dropdown()
            return
        if item == "Wizard":
            self.app.screen.show_wizard()
            self.close_dropdown()
            return

        
        if item == "Quit":
            self.app.exit()

        self.close_dropdown()

    # --------------------------------------------------------
    # KEY HANDLING (FIXED)
    # --------------------------------------------------------

    def on_key(self, event):

        # If dropdown is open — let dropdown handle keys
        if self.dropdown:
            return

        key = event.key

        # LEFT
        if key == "left":
            self.selected = (self.selected - 1) % len(self.items)
            self.label.update(self.render_menu())
            event.stop()
            return

        # RIGHT
        if key == "right":
            self.selected = (self.selected + 1) % len(self.items)
            self.label.update(self.render_menu())
            event.stop()
            return

        # ENTER — open dropdown
        if key == "enter":
            self.open_dropdown()
            event.stop()
            return
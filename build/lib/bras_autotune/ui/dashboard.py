from textual.app import App
from textual.screen import Screen
from textual.containers import Vertical

from bras_autotune.ui.menu import MenuBar
from bras_autotune.ui.screens import InterfacesView, InterfaceDetailsView
from bras_autotune.mon.live import LiveCPUView
from bras_autotune.mon.irq import IrqMonitor
from bras_autotune.ui.help_tuning import HelpTuningView
from bras_autotune.ui.wizard import WizardScreen


class DashboardScreen(Screen):

    def compose(self):
        yield MenuBar(id="menu")
        self.content = Vertical(id="content")
        yield self.content

    def on_mount(self):
        self.monitor = None
        self.query_one("#menu").focus()

    # ---------------------------------------------------------
    # Методы, которые вызывает MenuBar
    # ---------------------------------------------------------

    def show_interfaces(self, stats):
        self.content.remove_children()
        self.content.mount(InterfacesView(stats))
        self.monitor = None

    def show_interface_details(self, iface, stats):
        self.content.remove_children()
        self.content.mount(InterfaceDetailsView(iface, stats))
        self.monitor = None

    def show_live_monitoring(self):
        self.content.remove_children()
        self.content.mount(LiveCPUView())
        self.monitor = None

    def show_irq_monitoring(self):
        self.content.remove_children()
        self.monitor = IrqMonitor(self.app.current_iface)
        self.content.mount(self.monitor)

    def show_help_tuning(self):
        self.content.remove_children()
        self.content.mount(HelpTuningView())
        self.monitor = None

    def show_wizard(self):
        # ВАЖНО: WizardScreen — это Screen, его нельзя mount()
        self.app.push_screen(WizardScreen())


class DashboardApp(App):
    CSS_PATH = "dashboard.css"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from bras_autotune.mon.irq import detect_active_iface
        self.current_iface = detect_active_iface()

        # Эти данные нужны для интерфейсов
        self.interfaces_stats = {}

    def set_interface(self, iface):
        self.current_iface = iface

    def on_mount(self):
        self.push_screen(DashboardScreen())

    async def on_key(self, event):

        # ---------------------------------------------------------
        # Если открыт Wizard — игнорируем глобальные хоткеи
        # ---------------------------------------------------------
        if isinstance(self.screen, WizardScreen):
            return

        screen = self.screen
        menu = screen.query_one("#menu")

        # -----------------------------------------
        # ПРОБЕЛ — переключение интерфейсов в IRQ
        # -----------------------------------------
        if event.key == "space":
            if screen.monitor and isinstance(screen.monitor, IrqMonitor):
                screen.monitor.switch_iface()
                screen.monitor.focus()
            return

        # -----------------------------------------
        # СТРЕЛКА ВВЕРХ — фокус на меню
        # -----------------------------------------
        if event.key == "up":
            menu.focus()
            return

        # -----------------------------------------
        # СТРЕЛКИ ВЛЕВО/ВПРАВО — переключение пунктов меню
        # -----------------------------------------
        if event.key in ("left", "right"):
            if menu.has_focus:

                if event.key == "left":
                    screen.menu_index = (screen.menu_index - 1) % len(screen.menu_items)
                else:
                    screen.menu_index = (screen.menu_index + 1) % len(screen.menu_items)

                screen.open_menu_item()
                menu.focus()
            return
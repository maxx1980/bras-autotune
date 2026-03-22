from textual.app import App
from textual.screen import Screen
from textual.containers import Vertical

from bras_autotune.ui.menu import MenuBar
from bras_autotune.ui.screens import InterfacesView, InterfaceDetailsView
from bras_autotune.mon.live import LiveCPUView
from bras_autotune.mon.irq import IrqView

class DashboardScreen(Screen):

    def compose(self):
        # Верхнее меню
        yield MenuBar(id="menu")

        # Контейнер для сменяемого контента
        self.content = Vertical(id="content")
        yield self.content

    def show_interfaces(self, stats):
        """Показать список интерфейсов"""
        self.content.remove_children()
        self.content.mount(InterfacesView(stats))

    def show_interface_details(self, iface, stats):
        """Показать экран конкретного интерфейса"""
        self.content.remove_children()
        self.content.mount(InterfaceDetailsView(iface, stats))
        """ЛАЙВ"""
    def show_live_monitoring(self):
        self.content.remove_children()
        self.content.mount(LiveCPUView())


    def show_irq_monitoring(self):
        self.content.remove_children()

        iface = self.app.current_iface  # ← правильный источник интерфейса

        from bras_autotune.mon.irq import IrqMonitor
        self.content.mount(IrqMonitor(iface))



    def on_mount(self):
        self.query_one("#menu").focus()


class DashboardApp(App):
    CSS_PATH = "dashboard.css"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Текущий выбранный интерфейс
        from bras_autotune.mon.irq import detect_active_iface
        self.current_iface = detect_active_iface()

    def set_interface(self, iface):
        """Меню вызывает это при выборе интерфейса"""
        self.current_iface = iface

    def on_mount(self):
        self.push_screen(DashboardScreen())
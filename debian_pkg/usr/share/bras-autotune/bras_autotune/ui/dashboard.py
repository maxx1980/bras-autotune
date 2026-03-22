from textual.app import App
from textual.screen import Screen
from textual.containers import Vertical

from bras_autotune.ui.menu import MenuBar
from bras_autotune.ui.screens import InterfacesView, InterfaceDetailsView
from bras_autotune.mon.live import LiveCPUView


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


    def on_mount(self):
        self.query_one("#menu").focus()


class DashboardApp(App):
    CSS_PATH = "dashboard.css"

    def on_mount(self):
        self.push_screen(DashboardScreen())
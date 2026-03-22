from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static
from textual.containers import Horizontal, Vertical


class BrasAutotuneUI(App):
    CSS_PATH = "app.css"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("BRAS Autotune — Новый интерфейс", id="title")

        # Основные кнопки
        with Horizontal(id="menu"):
            yield Button("Интерфейсы", id="interfaces")
            yield Button("Настройки", id="settings")
            yield Button("Выход", id="exit")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id

        if button_id == "interfaces":
            self.push_screen(InterfacesScreen())

        elif button_id == "settings":
            self.push_screen(SettingsScreen())

        elif button_id == "exit":
            self.exit()


class InterfacesScreen(Static):
    def compose(self) -> ComposeResult:
        yield Static("Здесь будет список интерфейсов")


class SettingsScreen(Static):
    def compose(self) -> ComposeResult:
        yield Static("Здесь будут настройки")


def run_textual_ui():
    BrasAutotuneUI().run()

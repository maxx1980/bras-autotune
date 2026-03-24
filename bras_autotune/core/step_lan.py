# bras_autotune/core/step_lan.py

from textual.widgets import Static, Select
from textual.containers import Vertical


class StepLAN:
    title = "Выбор LAN интерфейса"

    def __init__(self):
        self._select = None

    def render(self, wizard):

        # Все интерфейсы
        interfaces = wizard.state.interfaces or []

        # Убираем WAN из списка
        wan = wizard.state.wan
        if wan in interfaces:
            interfaces = [iface for iface in interfaces if iface != wan]

        self._select = Select(
            options=[(iface, iface) for iface in interfaces],
            prompt="Выберите LAN интерфейс",
            id="lan_select",
        )

        step = self

        class StepContainer(Vertical):

            def on_mount(self_inner):
                step._select.focus()

            def on_select_changed(self_inner, event: Select.Changed):
                wizard.state.lan = event.value
                wizard.next_step()

        return StepContainer(
            Static("Выберите LAN интерфейс:", classes="step-title"),
            self._select,
            classes="step-container",
        )

    def collect(self, wizard):
        wizard.state.lan = self._select.value
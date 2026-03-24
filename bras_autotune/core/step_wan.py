from textual.widgets import Static, Select
from textual.containers import Vertical
from textual import events

class StepWAN:
    title = "Выбор WAN интерфейса"

    def __init__(self):
        self._select = None

    def render(self, wizard):

        interfaces = wizard.state.interfaces or []

        self._select = Select(
            options=[(iface, iface) for iface in interfaces],
#            prompt="Выберите WAN интерфейс",
            id="wan_select",
        )

        class StepContainer(Vertical):
            def on_mount(self_inner):
                self._select.focus()

            # Автоматический переход после выбора
            def on_select_changed(self_inner, event: Select.Changed):
                wizard.state.wan = event.value
                wizard.next_step()

        container = StepContainer(
            Static("Выберите WAN интерфейс:", classes="step-title"),
            self._select,
            classes="step-container",
        )

        return container

    def collect(self, wizard):
        wizard.state.wan = self._select.value
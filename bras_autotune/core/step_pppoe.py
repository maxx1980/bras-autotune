# bras_autotune/core/step_pppoe.py

from textual.widgets import Static, Select
from textual.containers import Vertical

class StepPPPoE:
    title = "Используется ли PPPoE?"

    def __init__(self):
        self._select = None

    def render(self, wizard):

        # Да / Нет
        self._select = Select(
            options=[
                ("Да", True),
                ("Нет", False),
            ],
#            prompt="PPPoE используется?",
            id="pppoe_select",
        )

        class StepContainer(Vertical):
            def on_mount(self_inner):
                # Автофокус на Select
                self._select.focus()

            # Автоматический переход после выбора
            def on_select_changed(self_inner, event: Select.Changed):
                wizard.state.pppoe = event.value
                wizard.next_step()

        container = StepContainer(
            Static("Используется ли PPPoE?", classes="step-title"),
            self._select,
            classes="step-container",
        )

        return container

    def collect(self, wizard):
        wizard.state.pppoe = self._select.value
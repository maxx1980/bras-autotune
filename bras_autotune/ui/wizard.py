# bras_autotune/ui/wizard.py

from typing import Optional

from textual.app import ComposeResult
from textual.widgets import Button, Static
from textual.containers import Vertical, Horizontal
from textual.message import Message

from bras_autotune.core.wizard_state import WizardState

# Шаги мастера
from bras_autotune.core.step_wan import StepWAN
from bras_autotune.core.step_lan import StepLAN
from bras_autotune.core.step_pppoe import StepPPPoE
from bras_autotune.core.step_isolation import StepIsolation
from bras_autotune.core.step_irqs import StepIRQs
from bras_autotune.core.step_txql import StepTXQL
from bras_autotune.core.step_summary import StepSummary


class WizardFinished(Message):
    def __init__(self, state: WizardState):
        super().__init__()
        self.state = state


class WizardView(Vertical):
    can_focus = True

    DEFAULT_CSS = """
    .wizard-title {
        text-align: center;
        padding: 1 0;
        height: 3;
        content-align: center middle;
        background: $surface;
        color: $text;
        border-bottom: solid $accent;
        dock: top;
    }

    .wizard-step-container {
        padding: 2;
        height: 1fr;
        content-align: left top;
    }

    .wizard-buttons {
        padding: 1;
        height: 3;
        content-align: center middle;
        border-top: solid $accent;
        background: $surface;
        dock: bottom;
    }

    .step-title {
        padding: 1 0;
        color: $accent;
        text-style: bold;
    }
    """

    def __init__(self):
        super().__init__()
        self.state = WizardState()

        # ФИКСИРОВАННЫЙ список шагов
        self.steps = [
            StepWAN(),
            StepLAN(),
            StepPPPoE(),
            StepIsolation(),
            StepIRQs(),
            StepTXQL(),
            StepSummary(),
        ]

        self.index = 0
        self._step_container = None
        self._title = None

    # ---------------------------------------------------------
    # UI layout
    # ---------------------------------------------------------

    def compose(self) -> ComposeResult:
        self._title = Static("", classes="wizard-title")
        self._step_container = Vertical(classes="wizard-step-container")

        buttons = Horizontal(
            Button("Назад", id="btn_back", variant="default"),
            Button("Далее", id="btn_next", variant="primary"),
            classes="wizard-buttons",
        )
        yield self._title
        yield self._step_container
#        yield buttons

    def on_mount(self):
        self.focus()
        self.load_step()

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def load_step(self):
        step = self.steps[self.index]

        self._title.update(step.title)

        self._step_container.remove_children()
        container = step.render(self)
        self._step_container.mount(container)

#        self.query_one("#btn_back").disabled = self.index == 0
#        self.query_one("#btn_next").label = (
#            "Готово" if self.index == len(self.steps) - 1 else "Далее"
#        )

    # ---------------------------------------------------------
    # Button handlers
    # ---------------------------------------------------------

 #   def on_button_pressed(self, event: Button.Pressed):
 #       if event.button.id == "btn_back":
 #           self.prev_step()
 #       elif event.button.id == "btn_next":
 #           self.next_step()

    def prev_step(self):
        if self.index > 0:
            self.index -= 1
            self.load_step()

    # ---------------------------------------------------------
    # NEXT STEP (с поддержкой skip)
    # ---------------------------------------------------------

    def next_step(self, skip: Optional[str] = None):
        step = self.steps[self.index]

        # Автоматические шаги НЕ вызывают collect()
        is_auto_step = hasattr(step, "auto") and step.auto

        if not is_auto_step:
            step.collect(self)

        # Переход вперёд
        if self.index < len(self.steps) - 1:
            self.index += 1

            # --- ПРОПУСК ШАГОВ ПО ИМЕНИ КЛАССА ---
            if skip:
                while (
                    self.index < len(self.steps)
                    and self.steps[self.index].__class__.__name__ == skip
                ):
                    self.index += 1

            self.load_step()
        else:
            self.post_message(WizardFinished(self.state))
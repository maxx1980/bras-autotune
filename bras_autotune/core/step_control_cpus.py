# bras_autotune/core/step_control_cpus.py

from textual.widgets import Static, Input
from textual.containers import Vertical


class StepControlCPUs:
    """
    Шаг выбора CPU для control‑plane.
    Минимальный интерфейс: render() + collect().
    """

    title = "Control‑plane CPU"

    def __init__(self):
        self._input = None

    def render(self, wizard):
        """
        Отрисовывает виджеты шага.
        """
        self._input = Input(
            placeholder="Например: 0-1",
            value=wizard.state.control_cpus or "",
            id="control_cpus",
        )

        container = Vertical(
            Static("Укажите CPU для control‑plane:", classes="step-title"),
            self._input,
            classes="step-container",
        )

        return container

    def collect(self, wizard):
        """
        Сохраняет выбранные CPU в wizard.state.
        """
        wizard.state.control_cpus = self._input.value.strip()

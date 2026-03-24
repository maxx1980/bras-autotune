# bras_autotune/core/step_data_cpus.py

from textual.widgets import Static, Input
from textual.containers import Vertical


class StepDataCPUs:
    """
    Шаг выбора CPU для data‑plane.
    Минимальный интерфейс: render() + collect().
    """

    title = "Data‑plane CPU"

    def __init__(self):
        self._input = None

    def render(self, wizard):
        """
        Отрисовывает виджеты шага.
        """
        self._input = Input(
            placeholder="Например: 2-5",
            value=wizard.state.data_cpus or "",
            id="data_cpus",
        )

        container = Vertical(
            Static("Укажите CPU для data‑plane:", classes="step-title"),
            self._input,
            classes="step-container",
        )

        return container

    def collect(self, wizard):
        """
        Сохраняет выбранные CPU в wizard.state.
        """
        wizard.state.data_cpus = self._input.value.strip()

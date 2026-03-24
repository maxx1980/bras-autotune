# bras_autotune/core/step_sysctl.py

from textual.widgets import Static, Input
from textual.containers import Vertical


class StepSysctl:
    """
    Шаг настройки sysctl параметров.
    Минимальный интерфейс: render() + collect().
    """

    title = "Sysctl параметры"

    def __init__(self):
        self._input = None

    def render(self, wizard):
        """
        Отрисовывает виджеты шага.
        """
        self._input = Input(
            placeholder="Например: net.core.rmem_max=26214400",
            value=wizard.state.sysctl_params or "",
            id="sysctl_params",
        )

        container = Vertical(
            Static("Укажите sysctl параметры (через пробел или перенос строки):", classes="step-title"),
            self._input,
            classes="step-container",
        )

        return container

    def collect(self, wizard):
        """
        Сохраняет sysctl параметры в wizard.state.
        """
        wizard.state.sysctl_params = self._input.value.strip()

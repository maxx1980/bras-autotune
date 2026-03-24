# bras_autotune/core/step_rps_xps.py

from textual.widgets import Static, Input, Button
from textual.containers import Vertical,Horizontal


class StepRPSXPS:
    """
    Шаг настройки RPS/XPS.
    Минимальный интерфейс: render() + collect().
    """

    title = "RPS / XPS"

    def __init__(self):
        self._rps = None
        self._xps = None

    def render(self, wizard):
        """
        Отрисовывает виджеты шага.

        """

        
        self._rps = Input(
            placeholder="RPS mask (например: ff)",
            value=wizard.state.rps_mask or "",
            id="rps_mask",
        )

        self._xps = Input(
            placeholder="XPS mask (например: ff)",
            value=wizard.state.xps_mask or "",
            id="xps_mask",
        )
        self._apply_btn = Button(
            "Сгенерировать конфиг",
            id="generate_irq_cfg_btn",
            variant="primary",
        )        
        container = Vertical(
            Static("Укажите маски RPS/XPS:", classes="step-title"),
            self._rps,
            self._xps,
            Horizontal(self._apply_btn),
            classes="step-container",
        )

        return container

    def collect(self, wizard):
        """
        Сохраняет значения в wizard.state.
        """
        wizard.state.rps_mask = self._rps.value.strip()
        wizard.state.xps_mask = self._xps.value.strip()

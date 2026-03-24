# bras_autotune/core/step_queues.py

from textual.widgets import Static, Input
from textual.containers import Vertical


class StepQueues:
    """
    Шаг настройки количества RX/TX очередей.
    Минимальный интерфейс: render() + collect().
    """

    title = "Настройка очередей"

    def __init__(self):
        self._rx = None
        self._tx = None

    def render(self, wizard):
        """
        Отрисовывает виджеты шага.
        """
        self._rx = Input(
            placeholder="RX очереди (например: 4)",
            value=str(wizard.state.rx_queues or ""),
            id="rx_queues",
        )

        self._tx = Input(
            placeholder="TX очереди (например: 4)",
            value=str(wizard.state.tx_queues or ""),
            id="tx_queues",
        )

        container = Vertical(
            Static("Укажите количество RX/TX очередей:", classes="step-title"),
            self._rx,
            self._tx,
            classes="step-container",
        )

        return container

    def collect(self, wizard):
        """
        Сохраняет значения в wizard.state.
        """
        rx = self._rx.value.strip()
        tx = self._tx.value.strip()

        wizard.state.rx_queues = int(rx) if rx.isdigit() else None
        wizard.state.tx_queues = int(tx) if tx.isdigit() else None

# bras_autotune/core/step_summary.py

from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal, VerticalScroll
import os

from bras_autotune.core.config_generator import ConfigGenerator


class StepSummary:
    title = "Summary"

    def __init__(self):
        self._save_btn = None
        self._status = None

    def render(self, wizard):
        s = wizard.state

        # Генерируем финальный конфиг
        cfg = ConfigGenerator(s)
        s.generated_full_config = cfg.generate_full()

        # Формируем текст итогов
        lines = [
            "Итоговая конфигурация:",
            "",
            f"WAN: {s.wan}",
            f"LAN: {s.lan}",
            "",
            f"Dataplane CPUs: {s.data_cpus}",
            f"Control CPUs: {s.control_cpus}",
            f"RX queues: {s.rx_queues}",
            f"TX queues: {s.tx_queues}",
            "",
            "IRQ affinity:",
            *[
                f"  Queue {irq['queue']}: "
                f"WAN {irq.get('wan_irq','')} → {irq.get('wan_mask','')}, "
                f"LAN {irq.get('lan_irq','')} → {irq.get('lan_mask','')}"
                for irq in (s.irqs or [])
            ],
            "",
            "RPS/XPS:",
            f"  RPS: {s.rps_mask}",
            f"  XPS: {s.xps_mask}",
            "",
            f"TX Queue Length: {s.tx_queue_len}",
            "",
            "Сгенерированный конфиг:",
            "",
            s.generated_full_config,
        ]

        summary_text = Static("\n".join(lines), classes="summary-text")

        # Кнопка сохранения
        self._save_btn = Button(
            "Сохранить конфиг",
            id="save_config_btn",
            variant="primary",
        )

        # Статус (успех/ошибка)
        self._status = Static("", classes="save-status")

        step = self

        class StepContainer(VerticalScroll):

            def on_button_pressed(self_inner, event: Button.Pressed):
                if event.button.id == "save_config_btn":
                    step._save_config(wizard)

        return StepContainer(
            summary_text,
            Horizontal(self._save_btn),
            self._status,
            classes="step-container",
        )

    # ---------------- Сохранение файла ----------------

    def _save_config(self, wizard):
        path = os.path.expanduser("~/bras_autotune.conf")

        try:
            with open(path, "w") as f:
                f.write(wizard.state.generated_full_config)

            self._status.update(f"Файл сохранён: {path}")

        except Exception as e:
            self._status.update(f"Ошибка сохранения: {e}")

    def collect(self, wizard):
        pass
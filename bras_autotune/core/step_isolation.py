from textual.widgets import Static, Input
from textual.containers import Vertical
from textual.events import Key


class StepIsolation:
    title = "Изоляция CPU"
    auto = True

    def __init__(self):
        self._input = None
        self._preview = None

    @staticmethod
    def make_mask(cpus):
        mask = 0
        for c in cpus:
            mask |= (1 << c)
        return hex(mask)

    def update_preview(self, text, cpu_count):
        text = text.strip()

        if text == "0":
            all_cpus = list(range(cpu_count))
            mask = self.make_mask(all_cpus)
            self._preview.update(f"Маска: {mask}")
            return

        try:
            if "-" in text:
                start_str, end_str = text.split("-", 1)
                start = int(start_str)
                end = int(end_str)
            else:
                start = int(text)
                end = start

            if start < 0 or end < 0 or start > end or end >= cpu_count:
                self._preview.update("Маска: — (ошибка)")
                return

            cpus = list(range(start, end + 1))
            mask = self.make_mask(cpus)
            self._preview.update(f"Маска: {mask}")

        except Exception:
            self._preview.update("Маска: —")

    def render(self, wizard):

        cpu_count = wizard.state.cpu_count or 0

        self._input = Input(
            placeholder="Введите диапазон: 1 или 1-4 или 0",
            value="0",
            id="cpu_range_input",
        )

        self._preview = Static("Маска: —", classes="mask-preview")

        step = self

        class StepContainer(Vertical):

            def on_mount(self_inner):
                step._input.focus()
                step.update_preview("0", cpu_count)

            async def on_key(self_inner, event: Key):
                text = step._input.value
                step.update_preview(text, cpu_count)

                if event.key != "enter":
                    return

                event.stop()
                text = text.strip()

                # -----------------------------
                # 0 → НЕТ ИЗОЛЯЦИИ → ПРОПУСКАЕМ StepIRQs
                # -----------------------------
                if text == "0":
                    all_cpus = list(range(cpu_count))

                    wizard.state.data_cpus = []
                    wizard.state.control_cpus = all_cpus

                    wizard.state.rx_queues = cpu_count
                    wizard.state.tx_queues = cpu_count

                    wizard.state.rps_mask = step.make_mask(all_cpus)
                    wizard.state.xps_mask = step.make_mask(all_cpus)

                    wizard.state.use_isolation = False

                    wizard.next_step()
                    return

                # -----------------------------
                # Диапазон → ИЗОЛЯЦИЯ ЕСТЬ → StepIRQs НУЖЕН
                # -----------------------------
                try:
                    if "-" in text:
                        start_str, end_str = text.split("-", 1)
                        start = int(start_str)
                        end = int(end_str)
                    else:
                        start = int(text)
                        end = start
                except Exception:
                    return

                if start < 0 or end < 0 or start > end or end >= cpu_count:
                    return

                dp_cpus = list(range(start, end + 1))
                cp_cpus = [i for i in range(cpu_count) if i not in dp_cpus]

                wizard.state.data_cpus = dp_cpus
                wizard.state.control_cpus = cp_cpus
                wizard.state.rx_queues = len(dp_cpus)
                wizard.state.tx_queues = len(dp_cpus)

                wizard.state.rps_mask = step.make_mask(dp_cpus)
                wizard.state.xps_mask = step.make_mask(dp_cpus)

                wizard.state.use_isolation = True

                wizard.next_step(skip="StepIRQs")

        return StepContainer(
            Static("Введите диапазон CPU для изоляции:", classes="step-title"),
            self._input,
            self._preview,
            classes="step-container",
        )

    def collect(self, wizard):
        pass
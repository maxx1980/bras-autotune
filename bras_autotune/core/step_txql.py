# bras_autotune/core/step_txql.py

from textual.widgets import Static, Input
from textual.containers import Vertical
from textual.events import Key


class StepTXQL:
    title = "TX Queue Length"

    def __init__(self):
        self._input = None
        self._wan_current = None
        self._lan_current = None

    # ---------------- Чтение текущего TXQL ----------------

    @staticmethod
    def read_txql(iface):
        if not iface:
            return None
        path = f"/sys/class/net/{iface}/tx_queue_len"
        try:
            with open(path) as f:
                return int(f.read().strip())
        except Exception:
            return None

    # ---------------- render ----------------

    def render(self, wizard):

        wan = wizard.state.wan
        lan = wizard.state.lan

        wan_txql = self.read_txql(wan)
        lan_txql = self.read_txql(lan)

        # WAN
        if wan:
            wan_text = f"WAN ({wan}) текущий TXQL: {wan_txql if wan_txql is not None else '–'}"
        else:
            wan_text = "WAN интерфейс не выбран"

        # LAN
        if lan:
            lan_text = f"LAN ({lan}) текущий TXQL: {lan_txql if lan_txql is not None else '–'}"
        else:
            lan_text = "LAN интерфейс не выбран"

        self._wan_current = Static(wan_text, classes="txql-current")
        self._lan_current = Static(lan_text, classes="txql-current")

        # Поле ввода — рекомендованное значение 10000
        self._input = Input(
            placeholder="Например: 10000",
            value="10000",
            id="tx_queue_len",
        )

        step = self

        class StepContainer(Vertical):

            def on_mount(self_inner):
                step._input.focus()   # автофокус

            async def on_key(self_inner, event: Key):
                if event.key != "enter":
                    return

                event.stop()

                value = step._input.value.strip()
                wizard.state.tx_queue_len = int(value) if value.isdigit() else None

                wizard.next_step()

        return StepContainer(
            Static("Укажите TX Queue Length:", classes="step-title"),
            self._wan_current,
            self._lan_current,
            self._input,
            classes="step-container",
        )

    def collect(self, wizard):
        pass
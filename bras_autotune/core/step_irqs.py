from textual.widgets import Static, Button, Input, DataTable
from textual.containers import Vertical, Horizontal, VerticalScroll
import re


class StepIRQs:
    title = "IRQ Affinity"

    def __init__(self):
        self._table = None
        self._apply_btn = None
        self._edit_inputs = {}   # q -> (wan_input, lan_input)

    # ---------------- /proc/interrupts ----------------

    @staticmethod
    def load_irqs():
        irqs = []
        try:
            with open("/proc/interrupts") as f:
                for line in f:
                    if ":" not in line:
                        continue
                    irq_str, rest = line.split(":", 1)
                    irq_str = irq_str.strip()
                    if not irq_str.isdigit():
                        continue
                    irq = int(irq_str)
                    parts = rest.strip().split()
                    if not parts:
                        continue
                    desc = parts[-1]
                    irqs.append({"irq": irq, "desc": desc})
        except Exception:
            pass
        return irqs

    @staticmethod
    def extract_queue(desc: str):
        m = re.search(r"txrx-(\d+)$", desc.lower())
        return int(m.group(1)) if m else None

    @staticmethod
    def read_effective_cpu(irq: int):
        try:
            path = f"/proc/irq/{irq}/effective_affinity"
            with open(path) as f:
                mask_hex = f.read().strip()
            mask = int(mask_hex, 16)
            if mask == 0:
                return None
            cpu = (mask & -mask).bit_length() - 1
            return cpu
        except Exception:
            return None

    @staticmethod
    def filter_iface_irqs(irqs, iface):
        iface = (iface or "").lower()
        out = []
        for irq in irqs:
            desc = irq["desc"].lower()
            if not re.search(r"txrx-\d+$", desc):
                continue
            if iface and iface in desc:
                out.append(irq)
        return out

    @staticmethod
    def merge_wan_lan_irqs(wan_irqs, lan_irqs):
        merged = {}
        for irq in wan_irqs:
            q = StepIRQs.extract_queue(irq["desc"])
            if q is None:
                continue
            merged.setdefault(q, {"queue": q})
            merged[q]["wan_irq"] = irq["irq"]
            merged[q]["wan_desc"] = irq["desc"]
            merged[q]["wan_cpu"] = StepIRQs.read_effective_cpu(irq["irq"])

        for irq in lan_irqs:
            q = StepIRQs.extract_queue(irq["desc"])
            if q is None:
                continue
            merged.setdefault(q, {"queue": q})
            merged[q]["lan_irq"] = irq["irq"]
            merged[q]["lan_desc"] = irq["desc"]
            merged[q]["lan_cpu"] = StepIRQs.read_effective_cpu(irq["irq"])

        rows = list(merged.values())
        rows.sort(key=lambda x: x["queue"])
        return rows

    # ---------------- render ----------------

    def render(self, wizard):

        all_irqs = self.load_irqs()
        wan_irqs = self.filter_iface_irqs(all_irqs, wizard.state.wan)
        lan_irqs = self.filter_iface_irqs(all_irqs, wizard.state.lan)

        rows = self.merge_wan_lan_irqs(wan_irqs, lan_irqs)
        wizard.state.irqs = rows

        # ---------------- Верхняя таблица ----------------

        self._table = DataTable(id="irq_table")
        self._table.add_columns(
            "WAN IRQ", "WAN desc", "WAN CPU",
            "LAN IRQ", "LAN desc", "LAN CPU"
        )

        for r in rows:
            self._table.add_row(
                str(r.get("wan_irq", "")),
                r.get("wan_desc", ""),
                "" if r.get("wan_cpu") is None else str(r["wan_cpu"]),
                str(r.get("lan_irq", "")),
                r.get("lan_desc", ""),
                "" if r.get("lan_cpu") is None else str(r["lan_cpu"]),
            )

        # ---------------- Нижняя таблица ----------------

        edit_rows = []

        # Заголовок
        edit_rows.append(
            Horizontal(
                Static("Queue", classes="col-q"),
                Static("WAN", classes="col-wan"),
                Static("new CPU", classes="col-q"),
                Static("LAN", classes="col-wan"),
                Static("new CPU", classes="col-q"),
                classes="edit-row",
            )
        )

        self._edit_inputs = {}

        dp = wizard.state.data_cpus or []
        first_input = None

        for r in rows:
            q = r["queue"]

            # -----------------------------
            # Рекомендованные значения
            # -----------------------------
            if dp:
                if q < len(dp):
                    rec_cpu = dp[q]
                else:
                    rec_cpu = dp[-1]
            else:
                rec_cpu = q

            wan_desc = r.get("wan_desc", "")
            lan_desc = r.get("lan_desc", "")

            wan_input = Input(id=f"wan_new_{q}", value=str(rec_cpu))
            lan_input = Input(id=f"lan_new_{q}", value=str(rec_cpu))

            if first_input is None:
                first_input = wan_input  # автофокус

            self._edit_inputs[q] = (wan_input, lan_input)

            edit_rows.append(
                Horizontal(
                    Static(str(q), classes="col-q"),
                    Static(wan_desc, classes="col-wan"),
                    wan_input,
                    Static(lan_desc, classes="col-lan"),
                    lan_input,
                    classes="edit-row",
                )
            )

        edit_block = Vertical(*edit_rows, id="edit_table")

        self._apply_btn = Button(
            "Сгенерировать конфиг",
            id="generate_irq_cfg_btn",
            variant="primary",
        )

        step = self
        focus_target = first_input

        class StepContainer(VerticalScroll):

            def on_mount(self_inner):
                if focus_target:
                    focus_target.focus()

            def on_button_pressed(self_inner, event: Button.Pressed):
                if event.button.id == "generate_irq_cfg_btn":
                    step._generate_config(wizard)
                    wizard.next_step()

        return StepContainer(
            Static("Текущие IRQ:", classes="step-title"),
            self._table,
            Static("Новая конфигурация:", classes="step-title"),
            edit_block,
            Horizontal(self._apply_btn),
        )

    # ---------------- Генерация конфига ----------------

    def _generate_config(self, wizard):
        lines = []

        for row in wizard.state.irqs:
            q = row["queue"]

            wan_input, lan_input = self._edit_inputs[q]

            wan_val = wan_input.value.strip()
            lan_val = lan_input.value.strip()

            if wan_val.isdigit() and row.get("wan_irq") is not None:
                mask = hex(1 << int(wan_val))
                row["wan_mask"] = mask
                lines.append(
                    f"echo {mask} > /proc/irq/{row['wan_irq']}/smp_affinity  # WAN queue {q}"
                )

            if lan_val.isdigit()and row.get("lan_irq") is not None:

                mask = hex(1 << int(lan_val))
                row["lan_mask"] = mask
                lines.append(
                    f"echo {mask} > /proc/irq/{row['lan_irq']}/smp_affinity  # LAN queue {q}"
                )

        wizard.state.generated_irq_config = "\n".join(lines)

    def collect(self, wizard):
        return
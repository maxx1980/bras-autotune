from textual.screen import Screen
from textual.widgets import Static, Input, Button
from textual.containers import Vertical
from textual.reactive import reactive
import psutil
import os

from bras_autotune.utils import list_physical_interfaces
from bras_autotune.core.config_generator import ConfigGenerator


class WizardState:
    def __init__(self):
        self.wan_iface = None
        self.lan_iface = None
        self.has_pppoe = False
        self.has_qinq = False
        self.use_isolation = False
        self.data_cpus = []
        self.control_cpus = []
        self.queues = None
        self.irq_map = {}
        self.rps_mask = None
        self.xps_mask = None
        self.sysctl = {}
        self.txql = 10000
        self.installed_apps = []
        self.selected_apps = []
        self.is_root = (os.geteuid() == 0)


class WizardScreen(Screen):

    step = reactive(0)

    def compose(self):
        with Vertical(id="wizard-container"):
            yield Static("", id="wizard-title")
            yield Static("", id="wizard-body")
            yield Input(placeholder="Введите ответ…", id="wizard-input")
            yield Button("Далее", id="wizard-next")

    def on_ready(self):
        print("WIZARD READY!")
        # DOM уже создан — теперь query_one() работает корректно
        self.title = self.query_one("#wizard-title", Static)
        self.body = self.query_one("#wizard-body", Static)
        self.input = self.query_one("#wizard-input", Input)
        self.next_btn = self.query_one("#wizard-next", Button)

        self.state = WizardState()

        # Подписка на изменение шага
        self.watch(self, "step", self.on_step_change)

        # Первичная отрисовка
        self.render_step()

    def on_step_change(self, *_):
        self.render_step()

    # -----------------------------
    # Валидация
    # -----------------------------
    def validate_iface(self, iface):
        return iface in list_physical_interfaces()

    def validate_cpu_list(self, lst):
        max_cpu = psutil.cpu_count()
        return all(0 <= x < max_cpu for x in lst)

    def recommend_cpu_split(self):
        total = psutil.cpu_count()
        half = total // 2
        return list(range(half, total)), list(range(0, half))

    # -----------------------------
    # Рендер шагов
    # -----------------------------
    def render_step(self):

        if self.step == 0:
            ifaces = list_physical_interfaces()
            self.title.update("[bold]Шаг 1: WAN интерфейс[/bold]")
            self.body.update(
                "Доступные интерфейсы:\n" +
                "\n".join(f"- {i}" for i in ifaces) +
                "\n\nВведите WAN интерфейс:"
            )
            return

        if self.step == 1:
            self.title.update("[bold]Шаг 1.2: LAN интерфейс[/bold]")
            self.body.update("Введите LAN интерфейс:")
            return

        if self.step == 2:
            self.title.update("[bold]Шаг 2: PPPoE[/bold]")
            self.body.update("Есть PPPoE? (yes/no)")
            return

        if self.step == 3:
            self.title.update("[bold]Шаг 3: CPU Isolation[/bold]")
            self.body.update("Использовать разделение data/control plane? (yes/no)")
            return

        if self.step == 4:
            if not self.state.use_isolation:
                self.step += 1
                return

            data, control = self.recommend_cpu_split()
            self.title.update("[bold]Шаг 4: CPU для data-plane[/bold]")
            self.body.update(
                f"Рекомендуемые CPU: {data}\n"
                "Введите CPU через запятую:"
            )
            return

        if self.step == 5:
            if not self.state.use_isolation:
                self.step += 1
                return

            data, control = self.recommend_cpu_split()
            self.title.update("[bold]Шаг 4.2: CPU для control-plane[/bold]")
            self.body.update(
                f"Рекомендуемые CPU: {control}\n"
                "Введите CPU через запятую:"
            )
            return

        if self.step == 6:
            self.title.update("[bold]Шаг 5: Очереди[/bold]")
            self.body.update("Введите количество очередей (или пусто для авто):")
            return

        if self.step == 7:
            self.title.update("[bold]Шаг 6: IRQ[/bold]")
            self.body.update("IRQ будут привязаны автоматически. Нажмите Далее.")
            return

        if self.step == 8:
            self.title.update("[bold]Шаг 7: RPS/XPS[/bold]")
            self.body.update("Генерируем маски. Нажмите Далее.")
            return

        if self.step == 9:
            self.title.update("[bold]Шаг 8: sysctl[/bold]")
            self.body.update("Генерируем sysctl. Нажмите Далее.")
            return

        if self.step == 10:
            self.title.update("[bold]Шаг 9: txqueuelen[/bold]")
            self.body.update("Введите txqueuelen (default 10000):")
            return

        if self.step == 11:
            self.title.update("[bold]Шаг 10: Приложения[/bold]")
            self.body.update("Сканируем приложения. Нажмите Далее.")
            return

        if self.step == 12:
            apps = ["systemd", "sshd", "pppd", "accel-ppp", "bird", "frr", "zabbix-agent"]
            self.state.installed_apps = apps

            self.title.update("[bold]Шаг 11: Выбор приложений[/bold]")
            self.body.update(
                "Выберите приложения для control-plane через запятую:\n" +
                ", ".join(apps)
            )
            return

        if self.step == 13:
            gen = ConfigGenerator(self.state)
            config_text = gen.generate_full()

            self.title.update("[bold]Предпросмотр конфига[/bold]")
            self.body.update(config_text)
            return

        if self.step == 14:
            self.title.update("[bold]Готово[/bold]")
            self.body.update("Конфиги сгенерированы.")
            self.input.visible = False
            self.next_btn.visible = False
            return

    # -----------------------------
    # Обработка ответов
    # -----------------------------
    def on_button_pressed(self, event):
        if event.button.id != "wizard-next":
            return

        ans = self.input.value.strip()

        if self.step == 0:
            if not self.validate_iface(ans):
                self.body.update("Ошибка: интерфейс не существует")
                return
            self.state.wan_iface = ans

        elif self.step == 1:
            if not self.validate_iface(ans):
                self.body.update("Ошибка: интерфейс не существует")
                return
            self.state.lan_iface = ans

        elif self.step == 2:
            self.state.has_pppoe = (ans.lower() == "yes")

        elif self.step == 3:
            self.state.use_isolation = (ans.lower() == "yes")

        elif self.step == 4:
            lst = [int(x) for x in ans.split(",")]
            if not self.validate_cpu_list(lst):
                self.body.update("Ошибка: неверные CPU")
                return
            self.state.data_cpus = lst

        elif self.step == 5:
            lst = [int(x) for x in ans.split(",")]
            if not self.validate_cpu_list(lst):
                self.body.update("Ошибка: неверные CPU")
                return
            self.state.control_cpus = lst

        elif self.step == 6:
            self.state.queues = int(ans) if ans else None

        elif self.step == 10:
            self.state.txql = int(ans)

        elif self.step == 12:
            self.state.selected_apps = [x.strip() for x in ans.split(",")]

        self.input.value = ""
        self.step += 1
# bras_autotune/core/wizard_state.py

class WizardState:
    """
    Хранилище всех параметров, которые пользователь выбирает
    на протяжении работы мастера.
    """

    def __init__(self):
        # Интерфейсы
        self.interfaces = []   # список строк
        self.wan = None
        self.lan = None

        # PPPoE
        self.pppoe = False

        self.cpu_count = 0          # ← ДОБАВИТЬ
        self.isolation = 0          # ← можно тоже добавить для ясности

        # CPU
        self.use_isolation = None
        self.cpu_isolation = ""
        self.data_cpus = ""
        self.control_cpus = ""

        # Очереди
        self.rx_queues = None
        self.tx_queues = None

        # IRQ
        self.irqs = []   # список словарей: { irq, desc, mask }

        # RPS/XPS
        self.rps_mask = ""
        self.xps_mask = ""

        # Sysctl
        self.sysctl_params = ""

        # TX Queue Length
        self.tx_queue_len = None

        # Приложения
        self.apps_dns = False
        self.apps_dhcp = False
        self.apps_radius = False


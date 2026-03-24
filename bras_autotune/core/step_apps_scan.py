# bras_autotune/core/step_apps_scan.py

from textual.widgets import Static, Checkbox
from textual.containers import Vertical


class StepAppsScan:
    """
    Шаг выбора приложений для автоконфигурации.
    Минимальный интерфейс: render() + collect().
    """

    title = "Сканирование приложений"

    def __init__(self):
        self._chk_dns = None
        self._chk_dhcp = None
        self._chk_radius = None

    def render(self, wizard):
        """
        Отрисовывает чекбоксы выбора сервисов.
        """
        self._chk_dns = Checkbox(
            label="DNS сервер",
            value=wizard.state.apps_dns,
            id="apps_dns",
        )

        self._chk_dhcp = Checkbox(
            label="DHCP сервер",
            value=wizard.state.apps_dhcp,
            id="apps_dhcp",
        )

        self._chk_radius = Checkbox(
            label="RADIUS сервер",
            value=wizard.state.apps_radius,
            id="apps_radius",
        )

        container = Vertical(
            Static("Выберите сервисы, которые нужно настроить:", classes="step-title"),
            self._chk_dns,
            self._chk_dhcp,
            self._chk_radius,
            classes="step-container",
        )

        return container

    def collect(self, wizard):
        """
        Сохраняет выбранные сервисы в wizard.state.
        """
        wizard.state.apps_dns = self._chk_dns.value
        wizard.state.apps_dhcp = self._chk_dhcp.value
        wizard.state.apps_radius = self._chk_radius.value

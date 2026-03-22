from textual.widgets import Static, DataTable
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from bras_autotune.tuning.recommendations import generate_interface_recommendations
from bras_autotune.tuning.offloads import (
    get_interface_offloads,
    get_offload_recommendations,
)
from bras_autotune.tuning.rps_xps import (
    get_rps_xps,
    get_rps_xps_recommendations,
)





class InterfacesView(Vertical):

    selected = reactive(0)

    def __init__(self, interfaces_stats):
        super().__init__()
        self.stats = interfaces_stats
        self.ifaces = list(interfaces_stats.keys())

    def compose(self):
        yield Static("Interfaces:", id="title")

        for iface in self.ifaces:
            item = Static(f"  {iface}", classes="iface-item")
            item.can_focus = True
            yield item

    def on_mount(self):
        self.highlight()
        self.focus()

    def highlight(self):
        items = self.query(".iface-item")
        for i, widget in enumerate(items):
            if i == self.selected:
                widget.update(f"> {self.ifaces[i]}")
                widget.add_class("selected")
            else:
                widget.update(f"  {self.ifaces[i]}")
                widget.remove_class("selected")

    def on_key(self, event):
        if event.key == "up":
            self.selected = max(0, self.selected - 1)
            self.highlight()

        elif event.key == "down":
            self.selected = min(len(self.ifaces) - 1, self.selected + 1)
            self.highlight()

        elif event.key == "enter":
            iface = self.ifaces[self.selected]
            from bras_autotune.ui.screens import InterfaceDetailsView
            self.parent.replace(InterfaceDetailsView(iface, self.stats[iface]))


class InterfaceDetailsView(Vertical):
#    DEFAULT_CSS = """
#    InterfaceDetailsView {
#        overflow-y: auto;
#    }
#    #left-pane {
#        width: 60%;
#        padding: 1 2;
#    }

#    #right-pane {
#        width: 40%;
#        padding: 1 2;
#    }
#
#    """
#    CSS_PATH = "screens.css"
    def __init__(self, iface, stats):
        super().__init__()
        self.iface = iface
        self.stats = stats

    def compose(self):
        yield Static(f"[bold]Интерфейс: {self.iface}[/bold]\n"
                     "[b]↑ back to menu[/b]\n"
                     )

        # Две колонки
        with Horizontal(id="details-columns"):

            # -------------------------------
            # Левая колонка — рекомендации
            # -------------------------------
            with Vertical(id="left-pane"):

                # --- Рекомендации по тюнингу ---
                yield Static("\n[u]Рекомендации по тюнингу:[/u]\n", classes="section-title")
                recs = generate_interface_recommendations(self.iface, self.stats)
                for r in recs:
                    yield Static("• " + r, classes="recommendation", markup=True)

                # --- Рекомендации по offloads ---
                yield Static("\n[u]Рекомендации по offloads:[/u]\n", classes="section-title")

                # WAN
                yield Static("\n[u]WAN оптимизация:[/u]\n", classes="section-title")
                wan_recs = get_offload_recommendations(self.iface, "wan")
                for r in wan_recs:
                    yield Static("• " + r, classes="recommendation")

                # PPPoE
                yield Static("\n[u]PPPoE оптимизация:[/u]\n", classes="section-title")
                pppoe_recs = get_offload_recommendations(self.iface, "pppoe")
                for r in pppoe_recs:
                    yield Static("• " + r, classes="recommendation")



            # -------------------------------
            # Правая колонка — таблица RPS/XPS
            # -------------------------------
            with Vertical(id="right-pane"):

                yield Static("\n[u]RPS/XPS:[/u]\n", classes="section-title")

                rpsxps = get_rps_xps(self.iface)

                table = DataTable(zebra_stripes=True)

                # Собираем номера очередей (0,1,2,3…)
                # Убираем префиксы rx- и tx-
                queues = sorted({
                    q.split("-")[1] for q in rpsxps["rps"].keys()
                } | {
                    q.split("-")[1] for q in rpsxps["xps"].keys()
                })

                # Добавляем колонки: "Que | 0 | 1 | 2 | 3"
                table.add_columns("Que", *queues)

                # RX строка
                rx_row = ["RX"]
                for q in queues:
                    key = f"rx-{q}"
                    rx_row.append(rpsxps["rps"].get(key, "—"))
                table.add_row(*rx_row)

                # TX строка
                tx_row = ["TX"]
                for q in queues:
                    key = f"tx-{q}"
                    tx_row.append(rpsxps["xps"].get(key, "—"))
                table.add_row(*tx_row)

                yield table


                                # --- Рекомендации по RPS/XPS ---
                yield Static("\n[u]Рекомендации по RPS/XPS:[/u]\n", classes="section-title")

                yield Static("[bold]WAN оптимизация:[/bold]")
                wan_rps = get_rps_xps_recommendations(self.iface, "wan")
                for r in wan_rps:
                    yield Static("• " + r, classes="recommendation")

                yield Static("\n[bold]PPPoE оптимизация:[/bold]")
                pppoe_rps = get_rps_xps_recommendations(self.iface, "pppoe")
                for r in pppoe_rps:
                    yield Static("• " + r, classes="recommendation")

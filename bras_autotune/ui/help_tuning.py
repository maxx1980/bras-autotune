from textual.widgets import Static
from textual.containers import Vertical


class HelpTuningView(Vertical):

    def compose(self):
        yield Static(
            """
[bold]Tuning Guide[/bold]

Этот раздел содержит рекомендации по оптимизации сетевых интерфейсов,
IRQ affinity, балансировке нагрузки и системных параметров. Пример для 8 ядер и
intel 520, enp1s0f0 смотрит в мир enp1s0f1 смотрит на клиентов

[b]Основные темы:[/b]
• Настройка IRQ affinity 
Определяем номера прерываний  
cat /proc/interrupts |grep enp1s0f

Прибиваем прерывания к ядрам где маска=номер ядра 
1-0 2-1 3-4 8-3 10-4 20-5 40-6 80-7

echo 1 > /proc/irq/126/smp_affinity #enp1s0f0-Rx-Tx0
echo 1 > /proc/irq/135/smp_affinity #enp1s0f1-Tx-Rx0

echo 2 > /proc/irq/127/smp_affinity #enp1s0f0-Rx-Tx1
echo 2 > /proc/irq/136/smp_affinity #enp1s0f1-Tx-Rx1

echo 4 > /proc/irq/128/smp_affinity #enp1s0f0-Rx-Tx2
echo 4 > /proc/irq/137/smp_affinity #enp1s0f1-Tx-Rx2

echo 8 > /proc/irq/129/smp_affinity #enp1s0f0-Rx-Tx3
echo 8 > /proc/irq/138/smp_affinity #enp1s0f1-Tx-Rx3

echo 10 > /proc/irq/130/smp_affinity #enp1s0f0-Rx-Tx4
echo 10 > /proc/irq/139/smp_affinity #enp1s0f1-Tx-Rx4

echo 20 > /proc/irq/131/smp_affinity #enp1s0f0-Rx-Tx5
echo 20 > /proc/irq/140/smp_affinity #enp1s0f1-Tx-Rx5

echo 40 > /proc/irq/132/smp_affinity #enp1s0f0-Rx-Tx6
echo 40 > /proc/irq/141/smp_affinity #enp1s0f1-Tx-Rx6

echo 80 > /proc/irq/133/smp_affinity #enp1s0f0-Rx-Tx7
echo 80 > /proc/irq/142/smp_affinity #enp1s0f1-Tx-Rx7

• XPS/RPS
XPS включается на обоих интерфейсах путем отсылания хекс маски,
для 8 ядер это ff
echo ff > /sys/class/net/enp1s0f0/queues/tx-0/xps_cpus
echo ff > /sys/class/net/enp1s0f0/queues/tx-1/xps_cpus
echo ff > /sys/class/net/enp1s0f0/queues/tx-2/xps_cpus
echo ff > /sys/class/net/enp1s0f0/queues/tx-3/xps_cpus
echo ff > /sys/class/net/enp1s0f0/queues/tx-4/xps_cpus
echo ff > /sys/class/net/enp1s0f0/queues/tx-5/xps_cpus
echo ff > /sys/class/net/enp1s0f0/queues/tx-6/xps_cpus
echo ff > /sys/class/net/enp1s0f0/queues/tx-7/xps_cpus

echo ff > /sys/class/net/enp1s0f1/queues/tx-0/xps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/tx-1/xps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/tx-2/xps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/tx-3/xps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/tx-4/xps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/tx-5/xps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/tx-6/xps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/tx-7/xps_cpus
RPS включается ТОЛЬКО на внутреннем интерфейсе и ТОЛЬКО в случае,
PPPOE и/или QinQ (с последним свои танцы, о чем позже).
Если есть PPPOE тогда
echo ff > /sys/class/net/enp1s0f1/queues/rx-0/rps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/rx-1/rps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/rx-2/rps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/rx-3/rps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/rx-4/rps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/rx-5/rps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/rx-6/rps_cpus
echo ff > /sys/class/net/enp1s0f1/queues/rx-7/rps_cpus
иначе
echo 0 > /sys/class/net/enp1s0f1/queues/rx-0/rps_cpus
echo 0 > /sys/class/net/enp1s0f1/queues/rx-1/rps_cpus
echo 0 > /sys/class/net/enp1s0f1/queues/rx-2/rps_cpus
echo 0 > /sys/class/net/enp1s0f1/queues/rx-3/rps_cpus
echo 0 > /sys/class/net/enp1s0f1/queues/rx-4/rps_cpus
echo 0 > /sys/class/net/enp1s0f1/queues/rx-5/rps_cpus
echo 0 > /sys/class/net/enp1s0f1/queues/rx-6/rps_cpus
echo 0 > /sys/class/net/enp1s0f1/queues/rx-7/rps_cpus
• ethtool
ethtool -g enp1s0f0
Pre-set maximums:
RX:             4096
RX Mini:        n/a
RX Jumbo:       n/a
TX:             4096
Current hardware settings:
RX:             2048
RX Mini:        n/a
RX Jumbo:       n/a
TX:             2048
Если Current < maximum
ethtool -G enp1s0f0 rx 4096
ethtool -G enp1s0f0 tx 4096
далее offloads
ethtool -K enp1s0f0 tso off gso off gro off rxvlan off txvlan off rx-vlan-filter off ntuple on tx-gso-partial off
ethtool -K enp1s0f1 tso off gso off gro off rxvlan off txvlan off rx-vlan-filter off ntuple on tx-gso-partial off
сушествуют мнения про то что настройка оффлоадов на внешенем и внутреннем интерфейас отличаются,
не могу утверждать, проверял зеркало, проблемы с скоростью отсутствуют, но вопрос нужно до изучать. 
ip link set enp1s0f0 txqueuelen 10000
ip link set enp1s0f1 txqueuelen 10000 по умолчанию он 1000 этого мало
• Настройки sysctl для высоких нагрузок
Опять же мнений очень много, все ситуативно, зависит от железа и степени агрессивности, 
опишу минимум который протестил на нагрузках 8-9 Gb\ps и 5 к сессий пппое.
/etc/sysctl.d/99-bras.conf

########## Core buffers ##########
net.core.rmem_max = 33554432
net.core.wmem_max = 33554432
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.core.optmem_max = 65536

########## NIC packet processing ##########
net.core.dev_weight = 256
net.core.dev_weight_rx_bias = 64
net.core.dev_weight_tx_bias = 32

########## Conntrack ##########
net.netfilter.nf_conntrack_max = 524288
net.netfilter.nf_conntrack_buckets = 131072

########## ARP ##########
net.ipv4.neigh.default.gc_thresh1 = 4096
net.ipv4.neigh.default.gc_thresh2 = 8192
net.ipv4.neigh.default.gc_thresh3 = 16384

########## IPv6 off (если не нужно) ##########
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

• более продвинуты тюнинг заключается в разделении ядер на,
дата плейн и контрол плейн
изолируем 2-7 ядра
/etc/default/grub
GRUB_CMDLINE_LINUX="isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7"
уменьшаем количество очередей сетевой до 6
ethtool -L enp1s0f0 combined 6
ethtool -L enp1s0f1 combined 6
прибиваем к 2-7 ядрам, это и будет наш датаплейн,
(если у вас проц с енергоээффективными ядрами, логика там обратная,
датаплейн вешается на 0-7 полные ядра, контрол на 8-11, слабые,
маска там соответственно другая)
echo 4 > /proc/irq/126/smp_affinity #enp1s0f0-Rx-Tx0
echo 4 > /proc/irq/142/smp_affinity #enp1s0f1-Tx-Rx0

echo 8 > /proc/irq/127/smp_affinity #enp1s0f0-Rx-Tx1
echo 8 > /proc/irq/143/smp_affinity #enp1s0f1-Tx-Rx1

echo 10 > /proc/irq/128/smp_affinity #enp1s0f0-Rx-Tx2
echo 10 > /proc/irq/144/smp_affinity #enp1s0f1-Tx-Rx2

echo 20 > /proc/irq/129/smp_affinity #enp1s0f0-Rx-Tx3
echo 20 > /proc/irq/145/smp_affinity #enp1s0f1-Tx-Rx3

echo 40 > /proc/irq/130/smp_affinity #enp1s0f0-Rx-Tx4
echo 40 > /proc/irq/146/smp_affinity #enp1s0f1-Tx-Rx4

echo 80 > /proc/irq/131/smp_affinity #enp1s0f0-Rx-Tx5
echo 80 > /proc/irq/147/smp_affinity #enp1s0f1-Tx-Rx5
маска считается по аналогии 
CPU0-2⁰-0x01
CPU1-2¹-0x02
CPU2-2²-0x04
CPU3-2³-0x08
CPU4-2⁴-0x10
CPU5-2⁵-0x20
CPU6-2⁶-0x40
CPU7-2⁷-0x80
CPU2-CPU7=0x04+0x08+0x10+0x20+0x40+0x80=0xfc или fc,
если например нужна маска для 2 4 6 ядра 0x04+0x10+0x40,
(свежие линухи не всегда хавают полный хекс 00fc,
и хотят короткий вид)
хекс маска для 2-7 ядра fc, она используется для rps\xps
если PPPOE включаем RPS 
MASK=fc
for i in /sys/class/net/enp1s0f1/queues/rx-*/rps_cpus; do
    echo $MASK > $i
done
иначе
MASK=0
for i in /sys/class/net/enp1s0f1/queues/rx-*/rps_cpus; do
    echo $MASK > $i
done
XPS на обоих интерфейсах
MASK=fc
for i in /sys/class/net/enp1s0f0/queues/tx-*/xps_cpus; do
    echo $MASK > $i
done
MASK=fc
for i in /sys/class/net/enp1s0f1/queues/tx-*/xps_cpus; do
    echo $MASK > $i
done
далее выносим приложение в контрол плейн добавляя опцию CPUAffinity
в systemd unit нужных приложений, 0 прибивает к 0 ядру, 0 1 к двум, 1 к 1.

[Service]
CPUAffinity=0 1
не забываем что нулевоя адро всегда нагружено больше, на нем много дефолтных
задач в статике и сменить цпу там нельзя. Что вынести, решать вам, 
попробую отсртировать по важности, первые 3 пункта просто хайли рекомендед. 
системные : systemd, journald, rsyslog, sshd, cron, dbus, acpid, kworkers
роутинг: BIRD / FRR / OSPF / BGP
доступ: pppd, accel-ppp, Radius client (auth/accounting)
ААА: FreeRADIUS client, CoA/DM, Session‑management daemons
мониторинг: Zabbix, Promrtheus, NetFlow exportes, snmpd
Что НЕЛЬЗЯ пускать на control plane (должно быть только на data plane):
❌ 1. Softirq NET_RX / NET_TX
Они должны работать на CPU2–7.
❌ 2. pppoe_rcv / ppp_input / netif_receive_skb
Это ядро BRAS.
❌ 3. conntrack / NAT / ip_forward
Это чистый data plane.
❌ 4. ixgbe IRQ
Все MSI‑X очереди должны быть на CPU2–7.
❌ 5. RPS/XPS
Только CPU2–7.
❌ 6. Fast‑path PPPoE session traffic
Никаких control‑plane процессов рядом.
Что получаем
- +20–40% PPS
- −15–30% CPU в pppoe_rcv
- минимальные softirq задержки
- стабильный BRAS под нагрузкой
- под ДДоС-ом остается управляемость приложениями в контрол плейне, 
ссш отзывался очень шустро, хотя ядра датаплейна были в полку, но даже что то, пытались роутить. 
- десктопные процессора Intel(R) Core(TM) i7-10900 терминировали клиентм 8-9 Gb+nat,
при равномерно загрузке ядер 50-60% в чнн.





Используйте стрелки для навигации и меню для переключения разделов.
            """,
            classes="help-text"
        )

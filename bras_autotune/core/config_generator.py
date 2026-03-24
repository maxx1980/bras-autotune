import os


class ConfigGenerator:

    def __init__(self, state):
        self.s = state

    # -----------------------------
    # CPU mask helper
    # -----------------------------
    def cpu_mask(self, cpus):
        mask = 0
        for c in cpus:
            mask |= (1 << c)
        return hex(mask)[2:]  # без 0x

    # -----------------------------
    # isolcpus
    # -----------------------------
    def gen_isolcpus(self):
        if not self.s.use_isolation:
            return "# CPU isolation disabled"

        cpus = ",".join(str(c) for c in self.s.data_cpus)
        return (
            'GRUB_CMDLINE_LINUX="'
            f"isolcpus={cpus} "
            f"nohz_full={cpus} "
            f"rcu_nocbs={cpus}"
            '"'
        )

    # -----------------------------
    # IRQ affinity
    # -----------------------------
    def gen_irq_affinity(self):
        if not getattr(self.s, "irqs", None):
            return "# IRQ affinity not generated"

        lines = ["# IRQ affinity"]

        for row in self.s.irqs:
            # WAN
            if "wan_irq" in row and "wan_mask" in row:
                mask = row["wan_mask"].replace("0x", "")
                lines.append(
                    f"echo {mask} > /proc/irq/{row['wan_irq']}/smp_affinity"
                )

            # LAN
            if "lan_irq" in row and "lan_mask" in row:
                mask = row["lan_mask"].replace("0x", "")
                lines.append(
                    f"echo {mask} > /proc/irq/{row['lan_irq']}/smp_affinity"
                )

        return "\n".join(lines)


    # -----------------------------
    # RPS
    # -----------------------------
    def gen_rps(self):
        # PPPoE включён?
        if not getattr(self.s, "pppoe", False):
            return (
                "# RPS disabled\n"
                f"for i in /sys/class/net/{self.s.lan}/queues/rx-*/rps_cpus; do echo 0 > $i; done"
            )

        # Если PPPoE — используем маску dataplane
        mask = self.s.rps_mask.replace("0x", "")

        return (
            "# RPS enabled\n"
            f"MASK={mask}\n"
            f"for i in /sys/class/net/{self.s.lan}/queues/rx-*/rps_cpus; do echo $MASK > $i; done"
        )


    # -----------------------------
    # XPS
    # -----------------------------
    def gen_xps(self):
        mask = self.s.xps_mask[2:] if self.s.xps_mask.startswith("0x") else self.s.xps_mask

        return (
            "# XPS\n"
            f"MASK={mask}\n"
            f"for i in /sys/class/net/{self.s.wan}/queues/tx-*/xps_cpus; do echo $MASK > $i; done\n"
            f"for i in /sys/class/net/{self.s.lan}/queues/tx-*/xps_cpus; do echo $MASK > $i; done"
        )

    # -----------------------------
    # sysctl
    # -----------------------------
    def gen_sysctl(self):
        return """# sysctl tuning
net.core.rmem_max = 33554432
net.core.wmem_max = 33554432
net.core.dev_weight = 256
net.core.dev_weight_rx_bias = 64
net.core.dev_weight_tx_bias = 32
net.netfilter.nf_conntrack_max = 524288
net.netfilter.nf_conntrack_buckets = 131072
"""

    # -----------------------------
    # txqueuelen
    # -----------------------------
    def gen_txql(self):
        txql = self.s.tx_queue_len
        return (
            "# txqueuelen\n"
            f"ip link set {self.s.wan} txqueuelen {txql}\n"
            f"ip link set {self.s.lan} txqueuelen {txql}"
        )

    # -----------------------------
    # Final config
    # -----------------------------
    def generate_full(self):
        return f"""
########################################
# BRAS AUTOTUNE CONFIG
########################################

# 1. isolcpus
{self.gen_isolcpus()}

# 2. IRQ affinity
{self.gen_irq_affinity()}

# 3. RPS
{self.gen_rps()}

# 4. XPS
{self.gen_xps()}

# 5. sysctl
{self.gen_sysctl()}

# 6. txqueuelen
{self.gen_txql()}
"""
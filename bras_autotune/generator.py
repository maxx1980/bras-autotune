from pathlib import Path
from bras_autotune.nic import detect_irqs_for_if

def generate_interfaces_snippet(cfg):
        out = Path(cfg["out_dir"]) / "interfaces.bras"
        if_wan = cfg["if_wan"]
        if_bras = cfg["if_bras"]

        data_mask = cfg["data_mask_hex"]
        data_list = cfg["data_cpu_list"]

        rxq_wan = cfg["rxq_wan"]
        rxq_bras = cfg["rxq_bras"]

        lines = []
        lines.append("# Auto-generated BRAS tuning")

        lines.append(f"auto {if_wan}")
        lines.append(f"iface {if_wan} inet manual")
        lines.append(f"    post-up ethtool -L {if_wan} combined {rxq_wan}")
        lines.append("")
        lines.append("    # XPS")
        for q in range(rxq_wan):
            lines.append(f"    post-up echo {data_mask} > /sys/class/net/{if_wan}/queues/tx-{q}/xps_cpus")
        lines.append("")

        lines.append(f"auto {if_bras}")
        lines.append(f"iface {if_bras} inet manual")
        lines.append(f"    post-up ethtool -L {if_bras} combined {rxq_bras}")
        lines.append("")
        lines.append("    # XPS")
        for q in range(rxq_bras):
            lines.append(f"    post-up echo {data_mask} > /sys/class/net/{if_bras}/queues/tx-{q}/xps_cpus")
        lines.append("")
        lines.append("    # RPS")
        for q in range(rxq_bras):
            lines.append(f"    post-up echo {data_mask} > /sys/class/net/{if_bras}/queues/rx-{q}/rps_cpus")
        lines.append("")
        lines.append("    # RFS")
        lines.append("    post-up echo 65536 > /proc/sys/net/core/rps_sock_flow_entries")
        for q in range(rxq_bras):
            lines.append(f"    post-up echo 8192 > /sys/class/net/{if_bras}/queues/rx-{q}/rps_flow_cnt")
        lines.append("")

        irqs = detect_irqs_for_if(if_bras)
        lines.append(f"    # RSS (IRQ affinity)")
        idx = 0
        for irq in irqs:
            core = data_list[idx]
            mask = format(1 << core, "x")
            lines.append(f"    post-up echo {mask} > /proc/irq/{irq}/smp_affinity")
            idx = (idx + 1) % len(data_list)
        lines.append("")

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(lines) + "")
        print(f"interfaces.bras → {out}")

def generate_cmdline_snippet(cfg):
        out = Path(cfg["out_dir"]) / "cmdline.txt"
        d = cfg["data_cores"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"isolcpus=0-{d-1} nohz_full=0-{d-1} rcu_nocbs=0-{d-1}")
        print(f"cmdline.txt → {out}")

def generate_systemd_pinning(cfg):
        out = Path(cfg["out_dir"]) / "systemd-pinning.sh"
        ctrl = " ".join(map(str, cfg["ctrl_cpu_list"]))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
        "#!/bin/bash\n"
        "SERVICES=(bird bird6 accel-ppp ssh sshd snmpd systemd-journald rsyslog cron)\n"
        "for SVC in \"${SERVICES[@]}\"; do\n"
        f"    systemctl set-property \"$SVC\".service AllowedCPUs={ctrl} || true\n"
        "done\n"

        )
        out.chmod(0o755)
        print(f"systemd-pinning.sh → {out}")

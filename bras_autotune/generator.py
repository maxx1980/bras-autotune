
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

    with open(out, "w", encoding="utf-8") as f:

        f.write("# Auto-generated BRAS tuning\n\n")

        # WAN
        f.write(f"auto {if_wan}\n")
        f.write(f"iface {if_wan} inet manual\n")
        f.write(f"    post-up ethtool -L {if_wan} combined {rxq_wan}\n\n")

        f.write("    # XPS\n")
        for q in range(rxq_wan):
            f.write(f"    post-up echo {data_mask} > /sys/class/net/{if_wan}/queues/tx-{q}/xps_cpus\n")
        f.write("\n")

        # BRAS
        f.write(f"auto {if_bras}\n")
        f.write(f"iface {if_bras} inet manual\n")
        f.write(f"    post-up ethtool -L {if_bras} combined {rxq_bras}\n\n")

        f.write("    # XPS\n")
        for q in range(rxq_bras):
            f.write(f"    post-up echo {data_mask} > /sys/class/net/{if_bras}/queues/tx-{q}/xps_cpus\n")
        f.write("\n")

        f.write("    # RPS\n")
        for q in range(rxq_bras):
            f.write(f"    post-up echo {data_mask} > /sys/class/net/{if_bras}/queues/rx-{q}/rps_cpus\n")
        f.write("\n")

        f.write("    # RFS\n")
        f.write("    post-up echo 65536 > /proc/sys/net/core/rps_sock_flow_entries\n")
        for q in range(rxq_bras):
            f.write(f"    post-up echo 8192 > /sys/class/net/{if_bras}/queues/rx-{q}/rps_flow_cnt\n")
        f.write("\n")

        # RSS
        f.write("    # RSS (IRQ affinity)\n")
        irqs = detect_irqs_for_if(if_bras)
        idx = 0
        for irq in irqs:
            core = data_list[idx]
            mask = format(1 << core, "x")
            f.write(f"    post-up echo {mask} > /proc/irq/{irq}/smp_affinity\n")
            idx = (idx + 1) % len(data_list)
        f.write("\n")

    print(f"interfaces.bras → {out}")


def generate_cmdline_snippet(cfg):
    out = Path(cfg["out_dir"]) / "cmdline.txt"
    d = cfg["data_cores"]

    with open(out, "w", encoding="utf-8") as f:
        f.write(f"isolcpus=0-{d-1} nohz_full=0-{d-1} rcu_nocbs=0-{d-1}\n")

    print(f"cmdline.txt → {out}")


def generate_systemd_pinning(cfg):
    out = Path(cfg["out_dir"]) / "systemd-pinning.sh"
    ctrl = " ".join(map(str, cfg["ctrl_cpu_list"]))

    with open(out, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write("SERVICES=(bird bird6 accel-ppp ssh sshd snmpd systemd-journald rsyslog cron)\n")
        f.write("for SVC in \"${SERVICES[@]}\"; do\n")
        f.write(f"    systemctl set-property \"$SVC\".service AllowedCPUs={ctrl} || true\n")
        f.write("done\n")

    out.chmod(0o755)
    print(f"systemd-pinning.sh → {out}")

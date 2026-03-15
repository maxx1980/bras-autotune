
from bras_autotune.dialog import interactive_select_ifaces_and_cores
from bras_autotune.nic import sync_cores_with_nic_queues
from bras_autotune.generator import (
    generate_interfaces_snippet,
    generate_cmdline_snippet,
    generate_systemd_pinning
)

def main():
    cfg = interactive_select_ifaces_and_cores()
    cfg = sync_cores_with_nic_queues(cfg)
    generate_interfaces_snippet(cfg)
    generate_cmdline_snippet(cfg)
    generate_systemd_pinning(cfg)

    print("\n=== ГОТОВО ===")
    print(f"Каталог с результатами: {cfg['out_dir']}")

import os
from bras_autotune.pe_detect import detect_pe_cores

def interactive_select_ifaces_and_cores():
        print("=== BRAS AUTOTUNE ===")

        if_wan = input("WAN интерфейс [enp1s0f0]: ").strip() or "enp1s0f0"
        if_bras = input("BRAS интерфейс [enp1s0f1]: ").strip() or "enp1s0f1"

        total = os.cpu_count() or 1
        print(f"Всего CPU: {total}")

        p, e = detect_pe_cores()
        auto = False

        if p or e:
            print(f"P-ядра: {p}")
            print(f"E-ядра: {e}")
            ans = input("Использовать P-ядра под DATA-plane? [Y/n]: ").strip() or "Y"
            if ans.lower().startswith("y"):
                data = len(p)
                ctrl = total - data
                auto = True
                print(f"DATA={data}, CONTROL={ctrl}")

        if not auto:
            while True:
                s = input("DATA-plane ядер: ").strip()
                if s.isdigit() and 1 <= int(s) < total:
                    data = int(s)
                    break

            ctrl = total - data

        return {
            "if_wan": if_wan,
            "if_bras": if_bras,
            "total_cores": total,
            "data_cores": data,
            "ctrl_cores": ctrl,
            "out_dir": "/root/bras-autotune",
        }

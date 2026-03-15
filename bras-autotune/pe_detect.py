
from bras_autotune.utils import run

def detect_pe_cores():
    try:
        out = run(["lscpu", "-e=CPU,MHZ"])
    except Exception:
        return [], []

    lines = out.splitlines()[1:]
    if not lines:
        return [], []

    cpu_mhz = []
    max_mhz = 0

    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        cpu = int(parts[0])
        try:
            mhz = float(parts[1])
        except ValueError:
            continue

        cpu_mhz.append((cpu, mhz))
        if mhz > max_mhz:
            max_mhz = mhz

    threshold = max_mhz - 500
    p = [cpu for cpu, mhz in cpu_mhz if mhz >= threshold]
    e = [cpu for cpu, mhz in cpu_mhz if mhz < threshold]

    return p, e

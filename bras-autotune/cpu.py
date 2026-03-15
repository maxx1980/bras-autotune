
def hex_mask_from_cpu_list(cpus):
    mask = 0
    for cpu in cpus:
        mask |= 1 << cpu
    return format(mask, "x")

def cpu_range(start, end):
    return list(range(start, end + 1))

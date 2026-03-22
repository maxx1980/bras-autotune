# coding=utf-8
import socket
import psutil
from collections import defaultdict, deque

from textual.containers import Vertical
from textual.widgets import Static
from textual.reactive import reactive



class SoftnetCPU:
    """Структура данных для одного CPU из /proc/net/softnet_stat"""

    __slots__ = (
        "cpu",
        "total",
        "dropped",
        "time_squeeze",
        "cpu_collision",
        "received_rps",
        "affinity",
    )

    def __init__(self, cpu, total, dropped, time_squeeze, cpu_collision, received_rps):
        self.cpu = cpu
        self.total = total
        self.dropped = dropped
        self.time_squeeze = time_squeeze
        self.cpu_collision = cpu_collision
        self.received_rps = received_rps

    @staticmethod
    def from_line(cpu, line):
        """Парсинг строки из /proc/net/softnet_stat"""
        fields = [int(x, 16) for x in line.split()]
        return SoftnetCPU(
            cpu=cpu,
            total=fields[0],
            dropped=fields[1],
            time_squeeze=fields[2],
            cpu_collision=fields[6],
            received_rps=fields[7],
        )

    def diff(self, prev):
        """Разница между текущим и предыдущим состоянием"""
        return SoftnetCPU(
            cpu=self.cpu,
            total=self.total - prev.total,
            dropped=self.dropped - prev.dropped,
            time_squeeze=self.time_squeeze - prev.time_squeeze,
            cpu_collision=self.cpu_collision - prev.cpu_collision,
            received_rps=self.received_rps - prev.received_rps,
        )


class SoftnetMonitor:
    """Менеджер чтения softnet_stat + история для авто‑масштабирования"""

    def __init__(self, history_len=60):
        self.history = {
            "total": defaultdict(lambda: deque(maxlen=history_len)),
            "dropped": defaultdict(lambda: deque(maxlen=history_len)),
            "time_squeeze": defaultdict(lambda: deque(maxlen=history_len)),
            "cpu_collision": defaultdict(lambda: deque(maxlen=history_len)),
            "received_rps": defaultdict(lambda: deque(maxlen=history_len)),
        }

        self.prev = self.read()

    @staticmethod
    def read():
        """Чтение текущего состояния softnet_stat"""
        stats = []
        with open("/proc/net/softnet_stat") as f:
            for cpu, line in enumerate(f):
                stats.append(SoftnetCPU.from_line(cpu, line))
        return stats

    def update(self):
        """Возвращает diff + обновляет историю"""
        now = self.read()
        diffs = []

        for cpu in range(len(now)):
            d = now[cpu].diff(self.prev[cpu])
            diffs.append(d)

            # обновляем историю
            self.history["total"][cpu].append(d.total)
            self.history["dropped"][cpu].append(d.dropped)
            self.history["time_squeeze"][cpu].append(d.time_squeeze)
            self.history["cpu_collision"][cpu].append(d.cpu_collision)
            self.history["received_rps"][cpu].append(d.received_rps)

        self.prev = now
        return diffs

    def max_history(self, key):
        """Максимум по истории для авто‑масштабирования"""
        values = self.history[key].values()
        return max((max(v) for v in values if len(v)), default=1)
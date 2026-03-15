
# BRAS Autotune
Автоматический генератор конфигов тюнинга BRAS/PPPoE с определением P/E ядер, синхронизацией очередей NIC и генерацией конфигураций.
RSS XPS RPS RFS

Проект рассчитан на Linux c установленными lscpu, ethtool и правами для записи в sysfs/procfs через post-up (обычно требуется root).

Установка пакета локально (editable):

git clone https://github.com/maxx1980/bras-autotune

cd bras-autotune

python3 -m venv .venv

source .venv/bin/activate

pip install -U pip

pip install -e .

Либо скачиваем пакет bras-autotune_1.0-1_all.deb 

dpkg -i bras-autotune_1.0-1_all.deb 

Запуск CLI: bras-autotune

спросит имена интерфейсов (WAN/BRAS), попытается определить P/E ядра через lscpu -e=CPU,MHZ, спросит распределение ядер, если автоопределение не спользуется, синхронизирует число очередей NIC с числом data-plane ядер, сгенерирует файлы:

interfaces.bras — фрагмент для сетевого конфигуратора (XPS/RPS/RFS/RSS),

cmdline.txt — параметры для ядра (isolcpus, nohz_full, rcu_nocbs),

systemd-pinning.sh — закрепление фоновых служб на control-ядрах.

Выходной каталог по умолчанию: /root/bras-autotune (как в задании).

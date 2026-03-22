
# BRAS Autotune
Автоматический генератор конфигов тюнинга BRAS/PPPoE с определением P/E ядер, синхронизацией очередей NIC и генерацией конфигураций.
RSS XPS RPS RFS, в последнем релизе експорт конфигов не реализован так как переписывалась вся логика и интерфейс, ТуДу некст релиз.

Проект рассчитан на Linux c установленными lscpu, ethtool и правами для записи в sysfs/procfs через post-up (обычно требуется root).

Установка пакета локально (editable):

git clone https://github.com/maxx1980/bras-autotune

cd bras-autotune

sudo apt install ./debian_pkg.deb

либо 
python3 -m venv .venv

source .venv/bin/activate

pip install -U pip

pip install -e .

Запуск TuI: bras-autotune


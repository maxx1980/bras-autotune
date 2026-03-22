
# BRAS Autotune
Автоматический генератор конфигов тюнинга BRAS/PPPoE с определением P/E ядер, синхронизацией очередей NIC и генерацией конфигураций.
RSS XPS RPS RFS, в последнем релизе експорт конфигов вырезан так как переписывалась вся логика и интерфейс, ТуДу некст релиз.

Проект рассчитан на Linux c установленными lscpu, ethtool и правами для записи в sysfs/procfs через post-up (обычно требуется root).

Установка пакета локально (editable):

git clone https://github.com/maxx1980/bras-autotune

cd bras-autotune

sudo apt install ./debian_pkg.deb

externally‑managed‑environment означает, що твоя система (Ubuntu/Debian) блокырует установку пакетов через pip3 install в системный Python.

лучще и правильнее 

python3 -m venv .venv

source .venv/bin/activate

pip install -U pip

pip install textual==0.50.1

pip install psutil

pip install -e .

звпуск bras-autotune

Запуск TuI: bras-autotune


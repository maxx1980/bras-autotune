import sys
import traceback
import logging
import os

from bras_autotune.generator import generate_config
from bras_autotune.fallback import fallback_mode
from bras_autotune.doctor import run_doctor
from bras_autotune.ui.app import run_textual_ui


# Логи
LOG_DIR = os.path.expanduser("~/.local/share/bras-autotune")
LOG_PATH = os.path.join(LOG_DIR, "bras-autotune.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def main():
    # -----------------------------
    # Команда bras-autotune doctor
    # -----------------------------
    if len(sys.argv) > 1 and sys.argv[1] == "doctor":
        run_doctor()
        return

    # -----------------------------
    # Запуск нового Textual UI
    # -----------------------------
    try:
        cfg = run_textual_ui()

        if not cfg:
            print("Операция отменена пользователем.")
            logging.info("User cancelled installer.")
            return

    except Exception as e:
        logging.error("Textual UI failed: %s", str(e))
        logging.error(traceback.format_exc())

        print("\nОшибка в интерфейсе. Переключаюсь в fallback режим.\n")
        cfg = fallback_mode()

    # -----------------------------
    # Генерация конфигурации
    # -----------------------------
    try:
        path = generate_config(cfg)

        logging.info("Config generated at: %s", path)

        print("\n=====================================")
        print("   BRAS AUTOTUNE — ГЕНЕРАЦИЯ ГОТОВА  ")
        print("=====================================\n")

        print(f" WAN интерфейс:     {cfg['if_wan']}")
        print(f" BRAS интерфейс:    {cfg['if_bras']}")
        print(f" DATA-plane cores:  {cfg['data_cores']}")
        print(f" CPU mask:          {cfg['data_mask_hex']}")
        print(f" Очереди WAN:       {cfg['rxq_wan']}")
        print(f" Очереди BRAS:      {cfg['rxq_bras']}")
        print(f" Файл сохранён:     {path}")

        print(f"\nЛог: {LOG_PATH}\n")

    except Exception as e:
        logging.error("Config generation failed: %s", str(e))
        logging.error(traceback.format_exc())
        print("\nОшибка генерации конфигурации. Подробности в логе.\n")
import sys
import traceback
import logging
import os


from bras_autotune.fallback import fallback_mode
from bras_autotune.doctor import run_doctor
from bras_autotune.ui.dashboard import DashboardApp


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
    # Запуск Textual UI
    # -----------------------------
    try:
        app = DashboardApp()
        app.run()

        # После закрытия UI можно получить конфиг, если ты его сохраняешь в app
        cfg = getattr(app, "result", None)

        if not cfg:
            print("Операция отменена пользователем.")
            logging.info("User cancelled installer.")
            return

    except Exception as e:
        logging.error("Textual UI failed: %s", str(e))
        logging.error(traceback.format_exc())

        print("\nОшибка в интерфейсе. Переключаюсь в fallback режим.\n")
        cfg = fallback_mode()

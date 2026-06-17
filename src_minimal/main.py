"""
Teams Translator - Main Entry Point
"""

import logging
import signal
import sys

from src_minimal.config_manager import CONFIG_DIR
from src_minimal.app_controller import TeamsTranslatorApp

LOG_DIR = CONFIG_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TeamsTranslator")


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    logger.info("=" * 50)
    logger.info("Teams Translator khoi dong...")
    logger.info("=" * 50)

    app = TeamsTranslatorApp()
    exit_code = app.start()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

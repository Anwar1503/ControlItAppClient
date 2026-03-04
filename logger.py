import logging
from logging.handlers import RotatingFileHandler
import os

APP_DIR = os.path.join(os.getenv("APPDATA"), "ControlIt")
LOG_DIR = os.getenv("LOG_DIR", os.path.join(APP_DIR, "logs"))
LOG_FILE = os.getenv("LOG_FILE", "agent.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def setup_logger(name: str) -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )

    # Console (optional, for --console builds)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File (primary for EXE)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Attach console only if running in console mode
    if os.getenv("ENABLE_CONSOLE_LOG", "0") == "1":
        logger.addHandler(console_handler)

    return logger

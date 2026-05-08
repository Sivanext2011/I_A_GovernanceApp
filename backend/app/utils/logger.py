import logging
from pathlib import Path
from app.config import settings

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG if settings.APP_DEBUG else logging.INFO)
        fh = logging.FileHandler(settings.LOG_DIR / "app.log")
        fh.setFormatter(logging.Formatter("%(asctime)s|%(name)s|%(levelname)s|%(message)s"))
        logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(sh)
    return logger

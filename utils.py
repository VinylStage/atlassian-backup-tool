# utils.py

import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")


def setup_logging(prefix: str) -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger(prefix)
    logger.addHandler(console_handler)
    return logger
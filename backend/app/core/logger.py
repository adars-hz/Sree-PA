import logging
from logging.handlers import RotatingFileHandler
import sys
from backend.app.core.config import settings

def setup_logger(name: str = "SREE"):
    """
    Configures a centralized rotating logger for SREE.
    Outputs to both console and a rotating log file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if logger is already configured
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler
    try:
        log_dir = settings.DATA_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "sree.log"

        # Max 5MB per file, keep 5 backups
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not initialize log file handler: {e}")

    return logger

# Global logger instance
logger = setup_logger()

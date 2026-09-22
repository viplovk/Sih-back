"""Structured logging configuration for ALGORIOT backend."""

import logging
import sys
import time
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure application-wide structured logger without secret leakage."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on re-init
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

    app_logger = logging.getLogger("algoriot")
    app_logger.setLevel(log_level)

    return app_logger


logger = setup_logging()

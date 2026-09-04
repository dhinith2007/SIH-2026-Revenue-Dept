import logging
import sys
from datetime import datetime, timezone
from app.core.config import settings


class Formatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.service = settings.SERVICE_NAME
        record.environment = settings.APP_ENV
        record.timestamp = datetime.now(timezone.utc).isoformat()
        return super().format(record)


def setup_logging() -> logging.Logger:
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(service)s] - %(message)s"
    formatter = Formatter(log_format)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if settings.APP_ENV != "development" else logging.DEBUG)
    
    # Avoid duplicate handlers if reloaded
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers[0] = handler

    logger = logging.getLogger(settings.SERVICE_NAME)
    logger.info(
        "Logging initialized for %s in %s environment",
        settings.SERVICE_NAME,
        settings.APP_ENV,
    )
    return logger


logger = logging.getLogger(settings.SERVICE_NAME)

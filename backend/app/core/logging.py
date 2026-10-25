"""Logging setup kept in one place so every module logs consistently."""

import logging

from app.core.config import Settings

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging(settings: Settings) -> None:
    """Configure root logging once, at application startup."""
    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT, force=True)
    # Keep noisy third-party loggers quieter unless we are debugging.
    if not settings.debug:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

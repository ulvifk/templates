import logging
from enum import IntEnum

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class LogLevel(IntEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def configure_logging(level: LogLevel) -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT, force=True)

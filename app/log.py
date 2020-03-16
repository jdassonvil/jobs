import logging
import os

from pythonjsonlogger import jsonlogger

LOG_FORMAT = "%(asctime)s %(name)s - %(levelname)s:%(message)s"

def _get_log_level():
    level_str = os.getenv("LOG_LEVEL", "info")

    if level_str == "debug":
        return logging.DEBUG
    else:
        return logging.INFO

def init_logger():
    log_level = _get_log_level()
    logger = logging.getLogger()
    logger.setLevel(log_level)

    formatter = jsonlogger.JsonFormatter(LOG_FORMAT)
    logHandler = logging.StreamHandler()
    logHandler.setFormatter(formatter)
    logHandler.setLevel(log_level)
    logger.addHandler(logHandler)
    logger.info("logger configured in {}".format(log_level))

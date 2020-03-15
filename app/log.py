import logging
from pythonjsonlogger import jsonlogger

LOG_FORMAT = "%(asctime)s %(name)s - %(levelname)s:%(message)s"

def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = jsonlogger.JsonFormatter(LOG_FORMAT)
    logHandler = logging.StreamHandler()
    logHandler.setFormatter(formatter)
    logHandler.setLevel(logging.INFO)
    logger.addHandler(logHandler)
    logger.info("logger configured")

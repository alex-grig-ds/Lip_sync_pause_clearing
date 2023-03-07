import logging
import datetime
import pathlib

from config import *

def get_logger(
        logger_name: str, logs_folder: str, log_level: str = "info", verbose: bool = True
    ) -> logging:
    """
    Get app logger.
    :param loggerName: str
    :param logsFolder: Folder for log files saving
    :param level: 'critical', 'error', 'info', 'warning', 'debug'
    :param verbose: True if verbose mode.
        If debug mode: put messages in stdout and log file.
        If not debug: put messages only in log file.
    :return: logger
    """
    if log_level == "info":
        level = logging.INFO
    elif log_level == "warning":
        level = logging.WARNING
    elif log_level == "critical":
        level = logging.CRITICAL
    elif log_level == "error":
        level = logging.ERROR
    elif log_level == "debug":
        level = logging.DEBUG
    else:
        raise ValueError
    formatter = logging.Formatter("%(asctime)s %(message)s")
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.handlers.clear()

    now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
    pathlib.Path(logs_folder).mkdir(parents=True, exist_ok=True)
    log_file = pathlib.Path(logs_folder, f"{logger_name}_{now}.log")
    output_file_handler = logging.FileHandler(log_file)
    output_file_handler.setFormatter(formatter)
    logger.addHandler(output_file_handler)

    if verbose:
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    return logger

logger = get_logger("correction_log", LOG_FOLDER)
test_logger = get_logger("test_log", TEST_LOG_FOLDER)

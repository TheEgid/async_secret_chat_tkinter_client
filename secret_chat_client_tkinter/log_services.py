import aiofiles
import logging
import os
from logging.handlers import RotatingFileHandler


watchdog_logger = logging.getLogger('watchdog')
broadcast_logger = logging.getLogger('broadcast')
history_logger = logging.getLogger('history')


def install_logs_parameters(log_path, logs=False):
    broadcast_logger.setLevel(logging.INFO)
    watchdog_logger.setLevel(logging.INFO)
    history_logger.setLevel(logging.INFO)
    os.makedirs(log_path, exist_ok=True)
    history_log_file = os.path.join(log_path, 'history.txt')
    history_file_handler = RotatingFileHandler(history_log_file,
                                               maxBytes=100000,
                                               backupCount=5,
                                               encoding="UTF-8")
    history_logger.addHandler(history_file_handler)

    if logs:
        broadcast_log_file = os.path.join(log_path, 'broadcast_logs.txt')
        broadcast_file_handler = RotatingFileHandler(broadcast_log_file,
                                                     maxBytes=100000,
                                                     backupCount=5,
                                                     encoding="UTF-8")
        watchdog_log_file = os.path.join(log_path, 'watchdog_logs.txt')
        watchdog_file_handler = RotatingFileHandler(watchdog_log_file,
                                                    maxBytes=100000,
                                                    backupCount=5,
                                                    encoding="UTF-8")
        log_formatter = logging.Formatter("[{asctime}] {message}",
                                          "%d-%m-%Y %H:%M:%S", "{")
        broadcast_file_handler.setFormatter(log_formatter)
        watchdog_file_handler.setFormatter(log_formatter)

        broadcast_logger.addHandler(broadcast_file_handler)
        watchdog_logger.addHandler(watchdog_file_handler)



async def load_log_from_file(log_path, log_filename='history.txt'):
    log_file = os.path.join(log_path, log_filename)
    log = []
    if os.path.exists(log_file):
        async with aiofiles.open(log_file, encoding="utf-8") as f:
            async for data in f:
                log.append(data)
    return log


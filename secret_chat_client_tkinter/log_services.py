import aiofiles
import logging
import os
from logging.handlers import RotatingFileHandler


watchdog_logger = logging.getLogger('watchdog')
broadcast_logger = logging.getLogger('broadcast')


def install_logs_parameters(log_path, logs=False):
    log_formatter = logging.Formatter("[{asctime}] {message}",
                                      "%d-%m-%Y %H:%M:%S", "{")
    broadcast_logger.setLevel(logging.INFO)
    watchdog_logger.setLevel(logging.INFO)

    if logs:
        os.makedirs(log_path, exist_ok=True)
        broadcast_log_file = os.path.join(log_path, 'broadcast_logs.txt')
        broadcast_file_handler = RotatingFileHandler(broadcast_log_file,
                                           maxBytes=100000,
                                           backupCount=5)
        watchdog_log_file = os.path.join(log_path, 'watchdog_logs.txt')
        watchdog_file_handler = RotatingFileHandler(watchdog_log_file,
                                           maxBytes=100000,
                                           backupCount=5)

        broadcast_file_handler.setFormatter(log_formatter)
        broadcast_logger.addHandler(broadcast_file_handler)
        watchdog_file_handler.setFormatter(log_formatter)
        watchdog_logger.addHandler(watchdog_file_handler)


async def log_to_file(data, log_path='chat_logs', log_filename='history.txt'):
    log_file = os.path.join(log_path, log_filename)
    log_info = f'{data}\n'
    async with aiofiles.open(log_file, 'a', encoding='utf8') as f:
        await f.write(log_info)


async def load_log_from_file(log_path='chat_logs', log_filename='history.txt'):
    log_file = os.path.join(log_path, log_filename)
    log = []
    if os.path.exists(log_file):
        async with aiofiles.open(log_file, encoding="utf-8") as f:
            async for data in f:
                log.append(data)
    return log


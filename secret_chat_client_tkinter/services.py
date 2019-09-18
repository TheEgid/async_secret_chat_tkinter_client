import aiofiles
import asyncio
import datetime
import pytz
import time
import socket
import logging
import sys
import os
import argparse
import aionursery
import contextlib


from logging.handlers import RotatingFileHandler

watchdog_loggrer = logging.getLogger('watchdog')
broadcast_logger = logging.getLogger('broadcast')


def install_logs_parameters(log_path, logs=False):
    log_formatter = logging.Formatter("[{asctime}] {message}",
                                      "%d-%m-%Y %H:%M:%S", "{")
    broadcast_logger.setLevel(logging.INFO)
    watchdog_loggrer.setLevel(logging.INFO)

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
        watchdog_loggrer.addHandler(watchdog_file_handler)


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


async def set_and_check_connection(host, port, pause_duration=5):
    counter = 0
    while True:
        try:
            counter += 1
            connection = await asyncio.open_connection(host=host, port=port)
            if connection:
                broadcast_logger.info('CONNECTION SUCCESSFUL')
                return connection
        except (socket.gaierror, ConnectionResetError, ConnectionError,
                ConnectionRefusedError, TimeoutError):
            broadcast_logger.info(f'CONNECTION ERROR! '
                              f'TRY CONNECT {counter} '
                              f'of {pause_duration}')
            time.sleep(pause_duration)
        if counter >= pause_duration:
            break


def sanitize_message(message):
    message = message.strip()
    message = message.replace('\n', ' ')
    return message


@contextlib.asynccontextmanager
async def create_handy_nursery():
    try:
        async with aionursery.Nursery() as nursery:
            yield nursery
    except aionursery.MultiError as e:
        if len(e.exceptions) == 1:
            raise e.exceptions[0]
        raise


def get_args_parser():
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter_class)

    parser.add_argument('-H', '--host', type=str,
                        default=os.getenv("HOST"),
                        help='chat connection hostname')

    parser.add_argument('-P', '--port_listener', type=int,
                        default=os.getenv("PORT_LISTENER"),
                        help='chat connection listener port')

    parser.add_argument('-f', '--folder_history', type=str,
                        default=os.getenv("FOLDER_HISTORY"),
                        help='filepath of chat history')

    parser.add_argument('-l', '--logs', action='store_true',
                        default=True,
                        help='set logging')
    return parser

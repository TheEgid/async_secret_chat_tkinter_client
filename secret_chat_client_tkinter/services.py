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

from logging.handlers import RotatingFileHandler


broadcast_logger = logging.getLogger('broadcast')


def install_logs_parameters(log_path, logs=False):
    log_formatter = logging.Formatter("[{asctime}] {message}",
                                      "%d-%m-%Y %H:%M:%S", "{")
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(log_formatter)
    broadcast_logger.setLevel(logging.INFO)
    broadcast_logger.addHandler(stream_handler)

    if logs:
        os.makedirs(log_path, exist_ok=True)
        log_file = os.path.join(log_path, 'chat_history.txt')
        file_handler = RotatingFileHandler(log_file,
                                           maxBytes=100000,
                                           backupCount=5)
        file_handler.setFormatter(log_formatter)
        broadcast_logger.addHandler(file_handler)


async def log_to_file(data, filepath='log.txt'):
    tz = pytz.timezone('Europe/Moscow')
    now = datetime.datetime.now(tz).strftime("%d-%m-%Y %H:%M:%S")
    log_info = f'[{now}] {data}\n'
    async with aiofiles.open(filepath, 'a', encoding='utf8') as logfile:
        await logfile.write(log_info)



async def set_and_check_connection(host, port):
    counter = 0
    pause_duration = 5
    while True:
        try:
            counter += 1
            connection = await asyncio.open_connection(host=host, port=port)
            if connection:
                await log_to_file('CONNECTION SUCCESSFUL')
                return connection
        except (socket.gaierror, ConnectionResetError, ConnectionError,
                ConnectionRefusedError, TimeoutError):
            await log_to_file(f'CONNECTION ERROR! '
                              f'TRY CONNECT {counter} '
                              f'of {pause_duration}')
            time.sleep(pause_duration)
        if counter >= pause_duration:
            break


def sanitize_message(message):
    message = message.strip()
    message = message.replace('\n', ' ')
    return message


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

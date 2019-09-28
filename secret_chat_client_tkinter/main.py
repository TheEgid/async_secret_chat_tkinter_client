import asyncio
import os
import async_timeout
import socket
from dotenv import load_dotenv
import tkinter.messagebox
from tkinter import *
import gui

from services import get_args_parser
from services import write_to_file
from services import ConnectionError, InvalidTokenError
from registration import get_new_username
from registration import register
from log_services import load_log_from_file
from log_services import install_logs_parameters
from log_services import watchdog_logger
from log_services import broadcast_logger
from log_services import history_logger
from helpers import set_and_check_connection
from helpers import authorise
from helpers import create_handy_nursery
from helpers import submit_message


async def save_history():
    while True:
        message = await _queues["history_queue"].get()
        if isinstance(message, str):
            history_logger.info(message)


async def send_message(stream_for_write):
    _queues["status_updates_queue"].put_nowait(
        gui.SendingConnectionStateChanged.ESTABLISHED)
    while True:
        message = await _queues["sending_queue"].get()
        if message:
            _queues["watchdog_queue"].put_nowait("Connection is alive. "
                                                 "Source: Message sender")
            await submit_message(stream_for_write, message)


async def ping_pong_connection(timeout, delay, stream_for_write):
    while True:
        try:
            await asyncio.sleep(delay)
            async with async_timeout.timeout(timeout):
                message = ""
                await submit_message(stream_for_write, message)
            _queues["watchdog_queue"].put_nowait("Connection is alive. "
                                                 "Source: Ping Pong")
        except socket.gaierror:
            raise ConnectionError


async def watch_for_connection(timeout_seconds):
    while True:
        async with async_timeout.timeout(timeout_seconds) as cm:
            watcher = await _queues["watchdog_queue"].get()
            if isinstance(watcher, str):
                watchdog_logger.info(watcher)
            if cm.expired:
                raise ConnectionError


async def broadcast_chat(stream_for_read, stream_for_write):
    reader, writer = stream_for_read
    reader2, writer2 = stream_for_write
    _queues["status_updates_queue"].put_nowait(
        gui.ReadConnectionStateChanged.ESTABLISHED)
    try:
        while True:
            data = await reader.read(1024)
            msg = data.decode().rstrip()
            if msg:
                _queues["messages_queue"].put_nowait(msg)
                _queues["history_queue"].put_nowait(msg)
                _queues["watchdog_queue"].put_nowait("Connection is alive. "
                                                     "Source: "
                                                     "New message in chat")
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        writer.close()
        writer2.close()


async def start_chat_process(stream_for_read, stream_for_write, token):
    authorisation_data = await authorise(stream_for_write, token)
    if not authorisation_data:
        broadcast_logger.info(f'NOT AUTORIZED WITH TOKEN "{token}"')
        raise InvalidTokenError
    _, _, nickname = authorisation_data
    event = gui.NicknameReceived(nickname)
    for _history in await load_log_from_file('chat_logs'):
        _queues["messages_queue"].put_nowait(_history.strip())
    _queues["status_updates_queue"].put_nowait(event)
    _queues["watchdog_queue"].put_nowait(f"Connection is alive. Source: "
                                         f"Authorisation as {nickname}")
    async with create_handy_nursery() as nursery:
        nursery.start_soon(broadcast_chat(stream_for_read,stream_for_write))
        nursery.start_soon(send_message(stream_for_write))
        nursery.start_soon(save_history())


async def get_connection_streams(host, port_sender, port_listener,
                                 pause_duration=5):
    stream_for_write = await set_and_check_connection(host, port_sender,
                                                      pause_duration)
    stream_for_read = await set_and_check_connection(host, port_listener,
                                                     pause_duration)
    return stream_for_read, stream_for_write


async def main():
    load_dotenv()
    parser = get_args_parser()
    args = parser.parse_args()
    install_logs_parameters('chat_logs', args.logs)

    CONNECTION_TIMEOUT_SECONDS = 15
    PING_PONG_CONNECTION_DELAY_SECONDS = 70

    token = os.getenv("TOKEN")
    host = os.getenv("HOST")
    port_sender = os.getenv("PORT_SENDER")
    port_listener = os.getenv("PORT_LISTENER")

    global _queues
    _queues = dict(messages_queue=asyncio.Queue(),
                   sending_queue=asyncio.Queue(),
                   history_queue=asyncio.Queue(),
                   status_updates_queue=asyncio.Queue(),
                   watchdog_queue=asyncio.Queue())

    stream_for_read, stream_for_write = await \
        get_connection_streams(host, port_sender, port_listener)

    if not token:
        new_username = get_new_username()
        if new_username:
            token, name = await register(stream_for_write, new_username)
            await write_to_file(f"\nTOKEN='{token}'", filepath='.env')
            _queues["watchdog_queue"].put_nowait(
                f"Connection is alive. Source: Registration as {name}")
            broadcast_logger.info(f'REGISTER AS "{name}" WITH TOKEN "{token}"')

            stream_for_read, stream_for_write = await \
                get_connection_streams(host, port_sender, port_listener)

    starter = start_chat_process(
        stream_for_write=stream_for_write,
        stream_for_read=stream_for_read,
        token=token)

    ping_ponger = ping_pong_connection(
        timeout=CONNECTION_TIMEOUT_SECONDS,
        delay=PING_PONG_CONNECTION_DELAY_SECONDS,
        stream_for_write=stream_for_write)

    try:
        async with create_handy_nursery() as nursery:
            nursery.start_soon(
                gui.draw(_queues["messages_queue"],
                         _queues["sending_queue"],
                         _queues["status_updates_queue"]))
            nursery.start_soon(starter)
            nursery.start_soon(watch_for_connection(CONNECTION_TIMEOUT_SECONDS))
            nursery.start_soon(ping_ponger)

    except InvalidTokenError:
        tkinter.messagebox.showerror("Неверный токен",
                                     "Проверьте токен, сервер его не узнал!")
        exit(1)
    except (asyncio.TimeoutError, ConnectionError, ConnectionResetError):
        tkinter.messagebox.showerror("Таймаут соединения",
                                     "Проверьте соединение с сетью!")
        exit(1)
    except (gui.TkAppClosed, KeyboardInterrupt):
        exit(0)


if __name__ == '__main__':
    asyncio.run(main())


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
from services import ConnectionError, InvalidTokenError, CancelledError, \
    MaximumRetryConnectionError
from registration import get_new_username
from registration import register
from log_services import load_log_from_file
from log_services import install_logs_parameters
from log_services import watchdog_logger
from log_services import broadcast_logger
from log_services import history_logger
from helpers import authorise
from helpers import create_handy_nursery
from helpers import submit_message


async def save_history():
    while True:
        message = await async_queues["history_queue"].get()
        if isinstance(message, str):
            history_logger.info(message)


async def send_message(stream_for_write):
    while True:
        message = await async_queues["sending_queue"].get()
        if message:
            async_queues["watchdog_queue"].put_nowait("Connection is alive. "
                                                      "Source: Message sender")
            await submit_message(stream_for_write, message)


async def ping_pong_connection(timeout, delay, stream_for_write):
    while True:
        try:
            await asyncio.sleep(delay)
            async with async_timeout.timeout(timeout):
                message = ""
                await submit_message(stream_for_write, message)
            async_queues["watchdog_queue"].put_nowait("Connection is alive. "
                                                      "Source: Ping Pong")
        except socket.gaierror:
            raise ConnectionError


async def watch_for_connection(timeout_seconds):
    while True:
        async with async_timeout.timeout(timeout_seconds) as cm:
            watcher = await async_queues["watchdog_queue"].get()
            if isinstance(watcher, str):
                watchdog_logger.info(watcher)
            if cm.expired:
                raise ConnectionError


async def broadcast_chat(stream_for_read, stream_for_write):
    reader, writer = stream_for_read
    reader2, writer2 = stream_for_write
    try:
        while True:
            data = await reader.read(1024)
            msg = data.decode().rstrip()
            if msg:
                async_queues["messages_queue"].put_nowait(msg)
                async_queues["history_queue"].put_nowait(msg)
                async_queues["watchdog_queue"].put_nowait(
                    "Connection is alive. Source: New message in chat")
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        async_queues["status_updates_queue"].put_nowait(
            gui.SendingConnectionStateChanged.CLOSED)
        async_queues["status_updates_queue"].put_nowait(
            gui.ReadConnectionStateChanged.CLOSED)
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
        async_queues["messages_queue"].put_nowait(_history.strip())
    async_queues["status_updates_queue"].put_nowait(event)
    async_queues["watchdog_queue"].put_nowait(f"Connection is alive. Source: "
                                              f"Authorisation as {nickname}")
    async with create_handy_nursery() as nursery:
        nursery.start_soon(broadcast_chat(stream_for_read,stream_for_write))
        nursery.start_soon(send_message(stream_for_write))
        nursery.start_soon(save_history())


async def get_connection_streams(host, port_sender, port_listener,
                                 connection_timeout_seconds,
                                 connection_max_retry):
    for counter in range(1, connection_max_retry+1):
        try:
            stream_for_write = await asyncio.open_connection(host=host,
                                                             port=port_sender)
            stream_for_read = await asyncio.open_connection(host=host,
                                                            port=port_listener)
            if stream_for_read and stream_for_write:
                broadcast_logger.info('CONNECTION SUCCESSFUL')
            return stream_for_read, stream_for_write
        except (socket.gaierror, ConnectionResetError, ConnectionError,
                ConnectionRefusedError, TimeoutError):
            broadcast_logger.info(f'CONNECTION ERROR! '
                                  f'TRY CONNECT {counter} '
                                  f'OF {connection_max_retry}')

            await asyncio.sleep(connection_timeout_seconds)
            if counter == connection_max_retry:
                raise MaximumRetryConnectionError


async def handle_connection(host, port_sender, port_listener, token):
    connection_timeout_seconds = 15
    connection_max_retry = 1000
    ping_pong_connection_delay_seconds = 70

    async with create_handy_nursery() as nursery:
        async_queues["status_updates_queue"].put_nowait(
            gui.ReadConnectionStateChanged.INITIATED)
        async_queues["status_updates_queue"].put_nowait(
            gui.SendingConnectionStateChanged.INITIATED)
        if not token:
            _, stream_for_write = await \
                get_connection_streams(host, port_sender, port_listener,
                                       connection_timeout_seconds,
                                       connection_max_retry)
            new_username = get_new_username()
            if new_username:
                token, name = await register(stream_for_write, new_username)
                await write_to_file(f"\nTOKEN='{token}'", filepath='.env')
                async_queues["watchdog_queue"].put_nowait(
                    f"Connection is alive. Source: Registration as {name}")
                broadcast_logger.info(
                    f'REGISTER AS "{name}" WITH TOKEN "{token}"')

        nursery.start_soon(
            gui.draw(async_queues["messages_queue"],
                     async_queues["sending_queue"],
                     async_queues["status_updates_queue"]))

        stream_for_read, stream_for_write = await \
            get_connection_streams(host, port_sender, port_listener,
                                   connection_timeout_seconds,
                                   connection_max_retry)
        nursery.start_soon(
            ping_pong_connection(
                timeout=connection_timeout_seconds,
                delay=ping_pong_connection_delay_seconds,
                stream_for_write=stream_for_write))

        nursery.start_soon(
            start_chat_process(
                stream_for_write=stream_for_write,
                stream_for_read=stream_for_read,
                token=token))

        nursery.start_soon(
            watch_for_connection(
                connection_timeout_seconds))

        async_queues["status_updates_queue"].put_nowait(
            gui.SendingConnectionStateChanged.ESTABLISHED)
        async_queues["status_updates_queue"].put_nowait(
            gui.ReadConnectionStateChanged.ESTABLISHED)


async def main():
    load_dotenv()
    parser = get_args_parser()
    args = parser.parse_args()
    token = os.getenv("TOKEN")
    host = os.getenv("HOST")
    port_sender = os.getenv("PORT_SENDER")
    port_listener = os.getenv("PORT_LISTENER")
    logs_folder = os.getenv("FOLDER_LOGS")

    install_logs_parameters(logs_folder, args.logs)

    global async_queues
    async_queues = dict(messages_queue=asyncio.Queue(),
                        sending_queue=asyncio.Queue(),
                        history_queue=asyncio.Queue(),
                        status_updates_queue=asyncio.Queue(),
                        watchdog_queue=asyncio.Queue())
    while True:
        try:
            await handle_connection(host, port_sender, port_listener, token)

        except InvalidTokenError:
            tkinter.messagebox.showerror(
                "Неверный токен ", "Проверьте токен, сервер его не узнал!")
            exit(1)

        except MaximumRetryConnectionError:
            tkinter.messagebox.showerror("Максимум попыток подключения. ",
                                         "Проверьте соединение с сетью!")
            exit(1)

        except (gui.TkAppClosed, KeyboardInterrupt):
            exit(0)

        except (socket.gaierror, ConnectionRefusedError, TimeoutError,
                ConnectionResetError, ConnectionResetError):
            continue


if __name__ == '__main__':
    asyncio.run(main())

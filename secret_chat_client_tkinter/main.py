import asyncio
import sys
import os
import async_timeout
import socket
from dotenv import load_dotenv
from tkinter import messagebox
import gui

from services import log_to_file
from services import install_logs_parameters
from services import set_and_check_connection
from gui import TkAppClosed
from services import get_args_parser
from services import create_handy_nursery, watchdog_loggrer, broadcast_logger
from chat_sender import ConnectionError, InvalidTokenError
from chat_sender import register, authorise, submit_message


# async def read_messages(reader, msgs_queue, save_queue, watchdog_queue):
#     while True:
#         message = await read_message(reader)
#         msgs_queue.put_nowait(message)
#         save_queue.put_nowait(message)
#         watchdog_queue.put_nowait('New message in chat')

async def save_messages():
    while True:
        msg = await _queues["history_queue"].get()
        await log_to_file(msg)


async def send_msgs(host, port, token):
    _queues["status_updates_queue"].put_nowait(
        gui.SendingConnectionStateChanged.ESTABLISHED)
    while True:
        message = await _queues["sending_queue"].get()
        if message:
            _queues["watchdog_queue"].put_nowait("Connection is alive. "
                                                 "Source: Msg sender")
            await submit_message(host, port, message, token)


async def ping_pong_connection(timeout, delay, host, port, token):
    while True:
        try:
            await asyncio.sleep(delay)
            async with async_timeout.timeout(timeout):
                message = ""
                await submit_message(host, port, message, token)
            _queues["watchdog_queue"].put_nowait("Connection is alive. "
                                                 "Source: Ping Pong")
        except socket.gaierror:
            raise ConnectionError


async def watch_for_connection(timeout_seconds):
    while True:
        async with async_timeout.timeout(timeout_seconds) as cm:
            watcher = await _queues["watchdog_queue"].get()
            if isinstance(watcher, str):
                watchdog_loggrer.info(watcher)
            if cm.expired:
                raise ConnectionError


async def broadcast_chat(host, port):
    reader, writer = await set_and_check_connection(host=host,
                                                    port=port,
                                                    pause_duration=5)
    _queues["status_updates_queue"].put_nowait(
        gui.ReadConnectionStateChanged.ESTABLISHED)
    try:
        while True:
            data = await reader.read(1024)
            msg = data.decode().rstrip()
            if msg:
                _queues["history_queue"].put_nowait(msg)
                _queues["messages_queue"].put_nowait(msg)
                _queues["watchdog_queue"].put_nowait("Connection is alive. "
                                                     "Source: "
                                                     "New message in chat")
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        writer.close()


async def start_chat_process(host, port_listener, port_sender, token):
    authorisation_data = await authorise(host, port_sender, token)
    if not authorisation_data:
        broadcast_logger.info(f'NOT AUTORIZED WITH TOKEN "{token}"')
        raise InvalidTokenError
    _, _, nickname = authorisation_data
    event = gui.NicknameReceived(nickname)
    _queues["status_updates_queue"].put_nowait(event)
    _queues["watchdog_queue"].put_nowait(f"Connection is alive. "
                                         f"Source: Authorisation as {nickname}")
    await broadcast_chat(host, port_listener)


    # await broadcast_chat(host, port_listener)
    #token, name = asyncio.run(coro_register)
    #print(f'registration name is {name}, token is {token}')

        # if not args.registration:
        #     while True:
        #         if not args.msg:
        #             print('Input your chat message here: ')
        #         message = input() if not args.msg else args.msg
        #
        #         if message:
        #             coro_send_message = submit_message(msg=message,
        #                                                host=args.host,
        #                                                port=args.port_sender,
        #                                                token=args.token)
        #
        #             asyncio.run(coro_send_message)
        #         if args.msg:
        #             break  # only single argument message!


async def main():
    load_dotenv()
    parser = get_args_parser()
    args = parser.parse_args()
    install_logs_parameters('chat_logs', args.logs)

    CONNECTION_TIMEOUT_SECONDS = 15
    PING_PONG_CONNECTION_DELAY_SECONDS = 70

    global _queues
    _queues = dict(messages_queue=asyncio.Queue(),
                  sending_queue=asyncio.Queue(),
                  history_queue=asyncio.Queue(),
                  status_updates_queue=asyncio.Queue(),
                  watchdog_queue=asyncio.Queue())

    sender = send_msgs(
        host=os.getenv("HOST"),
        port=os.getenv("PORT_SENDER"),
        token=os.getenv("TOKEN"))

    listener = start_chat_process(
        host=os.getenv("HOST"),
        port_listener=os.getenv("PORT_LISTENER"),
        port_sender=os.getenv("PORT_SENDER"),
        token=os.getenv("TOKEN"))

    ping_ponger = ping_pong_connection(
        timeout=CONNECTION_TIMEOUT_SECONDS,
        delay=PING_PONG_CONNECTION_DELAY_SECONDS,
        host=os.getenv("HOST"),
        port=os.getenv("PORT_SENDER"),
        token=os.getenv("TOKEN"))

    try:
        async with create_handy_nursery() as nursery:
            nursery.start_soon(
                gui.draw(_queues["messages_queue"],
                         _queues["sending_queue"],
                         _queues["status_updates_queue"]))
            nursery.start_soon(sender)
            nursery.start_soon(listener)
            nursery.start_soon(save_messages())
            nursery.start_soon(watch_for_connection(CONNECTION_TIMEOUT_SECONDS))
            nursery.start_soon(ping_ponger)

    except InvalidTokenError:
        messagebox.showerror("Неверный токен",
                             "Проверьте токен, сервер его не узнал!")
        exit(1)
    except (asyncio.TimeoutError, ConnectionError, ConnectionResetError):
        messagebox.showerror("Таймаут соединения",
                             "Проверьте соединение с сетью!")
        exit(1)
    except (TkAppClosed, KeyboardInterrupt):
        exit(0)


if __name__ == '__main__':
    asyncio.run(main())


import asyncio
import sys
import os

import gui
import aionursery

from services import log_to_file
from services import install_logs_parameters
from services import set_and_check_connection
from services import broadcast_logger

from services import get_args_parser
from chat_sender import AutorisationError, register, authorise, submit_message

from dotenv import load_dotenv


async def save_messages(queue, filepath='chat_logs'):
    filepath = os.path.join(filepath, 'chat_history.txt')
    while True:
        msg = await queue.get()
        await log_to_file(msg, filepath)


async def send_msgs(host, port, token):
    queues["status_updates_queue"].put_nowait(
        gui.SendingConnectionStateChanged.ESTABLISHED)
    while True:
        message = await queues["sending_queue"].get()
        await submit_message(host, port, message, token)


async def broadcast_chat(host, port):
    reader, writer = await set_and_check_connection(host=host, port=port)
    queues["status_updates_queue"].put_nowait(
        gui.ReadConnectionStateChanged.ESTABLISHED)
    try:
        while True:
            data = await reader.read(1024)
            msg = data.decode().rstrip()
            if msg:
                queues["history_queue"].put_nowait(msg)
                queues["messages_queue"].put_nowait(msg)
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        writer.close()


async def start_chat_process(host, port_listener, port_sender, token):
    reader, writer, nickname = await authorise(host, port_sender, token)
    if not reader:
        await log_to_file(f'NOT AUTORIZED WITH TOKEN "{token}"')
        raise AutorisationError
    event = gui.NicknameReceived(nickname)
    queues["status_updates_queue"].put_nowait(event)
    print(f'Выполнена авторизация. Пользователь {nickname}.')
    await broadcast_chat(host, port_listener)
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

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    global queues
    queues = dict(messages_queue=messages_queue,
                  sending_queue=sending_queue,
                  history_queue=history_queue,
                  status_updates_queue=status_updates_queue)

    sender = send_msgs(
        host=os.getenv("HOST"),
        port=os.getenv("PORT_SENDER"),
        token=os.getenv("TOKEN"))

    listener = start_chat_process(
        host=os.getenv("HOST"),
        port_listener=os.getenv("PORT_LISTENER"),
        port_sender=os.getenv("PORT_SENDER"),
        token=os.getenv("TOKEN"))

    try:
        async with aionursery.Nursery() as nursery:
            nursery.start_soon(gui.draw(messages_queue, sending_queue, status_updates_queue))
            nursery.start_soon(listener)
            nursery.start_soon(sender)
            nursery.start_soon(save_messages(history_queue))

    except gui.TkAppClosed: #, aionursery.MultiError):
        exit(0)


if __name__ == '__main__':
    asyncio.run(main())


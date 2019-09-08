import asyncio
import sys
import os
import json
import gui

from services import log_to_file
from services import install_logs_parameters
from services import sanitize_message
from services import set_and_check_connection
from services import broadcast_logger

from chat_sender import AutorisationError, get_args_parser


from dotenv import load_dotenv


async def submit_message(host, port, msg, token):
    reader, writer = await authorise(host, port, token)
    try:
        msg = sanitize_message(msg)
        end_of_msg = ''
        writer.write(str.encode(f'{msg}\n'))
        writer.write(str.encode(f'{end_of_msg}\n'))
        await writer.drain()
        await log_to_file(f'MESSAGE SENDED "{msg}"')
    finally:
        writer.close()


async def authorise(host, port, token):
    reader, writer = await set_and_check_connection(host=host, port=port)
    await reader.readline()
    writer.write(str.encode(f'{token}\n'))
    await writer.drain()
    reply = await reader.readline()
    try:
        authorization_success_msg = json.loads(reply.decode())
        if not authorization_success_msg:
            await log_to_file(f'NOT AUTORIZED WITH TOKEN "{token}"')
            raise AutorisationError

        nickname = authorization_success_msg['nickname']

        event = gui.NicknameReceived(nickname)
        status_updates_queue.put_nowait(event)

        await log_to_file(f'AUTORIZED AS "{nickname}"')
        return reader, writer

    except json.decoder.JSONDecodeError:
        await log_to_file(f'NOT AUTORIZED WITH TOKEN "{token}"')
        raise AutorisationError


async def broadcast_chat(host, port, queue):
    reader, writer = await set_and_check_connection(host=host, port=port)
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
    try:
        while True:
            data = await reader.read(1024)
            msg = data.decode().rstrip()
            if msg:
                broadcast_logger.info(msg)
                queue.put_nowait(msg)
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        writer.close()


async def send_msgs(host, port, queue):
    status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
    while True:
        message = await queue.get()
        await submit_message(host, port, message, token=os.getenv("TOKEN"))


def main():
    load_dotenv()
    parser = get_args_parser()
    args = parser.parse_args()
    install_logs_parameters('chat_logs', args.logs)

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()

    global status_updates_queue
    status_updates_queue = asyncio.Queue()


    my_message = send_msgs(
        host=os.getenv("HOST"),
        port=os.getenv("PORT_SENDER"),
        queue=sending_queue)

    listener = broadcast_chat(
        host=os.getenv("HOST"),
        port=os.getenv("PORT_LISTENER"),
        queue=messages_queue)

    try:
        main_gui = gui.draw(messages_queue, sending_queue, status_updates_queue)
        chat_process = asyncio.gather(main_gui, listener, my_message)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(chat_process)

    except gui.TkAppClosed:
        exit(0)


if __name__ == '__main__':
    main()


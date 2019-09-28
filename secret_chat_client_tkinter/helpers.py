import json
import asyncio
import aionursery
import contextlib
import time
import socket

from services import sanitize_message
from log_services import broadcast_logger


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


@contextlib.asynccontextmanager
async def create_handy_nursery():
    try:
        async with aionursery.Nursery() as nursery:
            yield nursery
    except aionursery.MultiError as e:
        if len(e.exceptions) == 1:
            raise e.exceptions[0]
        raise


def get_account_hash_and_nickname(registration_data):
    try:
        reply_json = json.loads(registration_data)
        return reply_json['account_hash'], reply_json['nickname']
    except json.decoder.JSONDecodeError:
        return None


async def authorise(stream_for_write, token):
    reader, writer = stream_for_write
    await reader.readline()
    writer.write(str.encode(f'{token}\n'))
    await writer.drain()
    reply = await reader.readline()
    try:
        authorization_success_msg = json.loads(reply.decode())
        if not authorization_success_msg:
            return None
        nickname = authorization_success_msg['nickname']
        broadcast_logger.info(f'AUTORIZED AS "{nickname}"')
        return reader, writer, nickname
    except json.decoder.JSONDecodeError:
        return None


async def submit_message(stream_for_write, msg):
    reader, writer = stream_for_write
    msg = sanitize_message(msg)
    end_of_msg = ''
    writer.write(str.encode(f'{msg}\n'))
    writer.write(str.encode(f'{end_of_msg}\n'))
    await writer.drain()
    if msg:
        broadcast_logger.info(f'MESSAGE SENDED "{msg}"')


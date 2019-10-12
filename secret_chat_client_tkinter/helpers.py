import json
import aionursery
import contextlib

from services import sanitize_message
from log_services import broadcast_logger


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

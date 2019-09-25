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


async def register(new_name, host, port):
    hash_and_nickname = None
    attempts = 5
    reader, writer = await set_and_check_connection(host=host, port=port)
    try:
        writer.write(b'\n')
        await writer.drain()
        if await reader.readline():
            _name = str.encode(f'{new_name}\n')
            writer.write(_name)
            await writer.drain()
            await reader.readline()
            registration_data = await reader.readline()
            for attempt in range(attempts):
                hash_and_nickname = \
                    get_account_hash_and_nickname(registration_data)
                if hash_and_nickname:
                    break
        return hash_and_nickname
    except UnicodeDecodeError:
        pass
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
            return None
        nickname = authorization_success_msg['nickname']
        broadcast_logger.info(f'AUTORIZED AS "{nickname}"')
        return reader, writer, nickname
    except json.decoder.JSONDecodeError:
        return None


async def submit_message(host, port, msg, token):
    reader, writer, _ = await authorise(host, port, token)
    try:
        msg = sanitize_message(msg)
        end_of_msg = ''
        writer.write(str.encode(f'{msg}\n'))
        writer.write(str.encode(f'{end_of_msg}\n'))
        await writer.drain()
        if msg:
            broadcast_logger.info(f'MESSAGE SENDED "{msg}"')
    finally:
        writer.close()



# def main():
#     load_dotenv()
#     parser = get_args_parser()
#     args = parser.parse_args()
#     install_logs_parameters(args.logs)
#     try:
#         if args.registration:
#             coro_register = register(new_name=args.msg,
#                                      host=args.host,
#                                      port=args.port_sender)
#             token, name = asyncio.run(coro_register)
#             args.token = token
#             args.user = name
#             args.registration = False
#             args.msg = None
#             print(f'registration name is {name}, token is {token}')
#
#         if not args.registration:
#             while True:
#                 if not args.msg:
#                     print('Input your chat message here: ')
#                 message = input() if not args.msg else args.msg
#
#                 if message:
#                     coro_send_message = submit_message(msg=message,
#                                                        host=args.host,
#                                                        port=args.port_sender,
#                                                        token=args.token)
#                     asyncio.run(coro_send_message)
#                 if args.msg:
#                     break  # only single argument message!
#
#     except KeyboardInterrupt:
#         sys.exit(1)
#
#
# if __name__ == '__main__':
#     main()

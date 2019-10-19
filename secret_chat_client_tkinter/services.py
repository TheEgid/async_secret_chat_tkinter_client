import os
import aiofiles
import argparse
import json


tkinter_window_is_open = False


class CancelledError(Exception):
    pass


class ConnectionError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


async def write_to_file(data, filepath):
    async with aiofiles.open(filepath, 'a', encoding='utf8') as logfile:
        await logfile.write(data)

    
def get_account_hash_and_nickname(registration_data):
    try:
        reply_json = json.loads(registration_data)
        return reply_json['account_hash'], reply_json['nickname']
    except json.decoder.JSONDecodeError:
        return None

    
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
    parser.add_argument('-Pl', '--port_listener', type=int,
                        default=os.getenv("PORT_LISTENER"),
                        help='chat connection listener port')
    parser.add_argument('-Ps', '--port_sender', type=int,
                        default=os.getenv("PORT_SENDER"),
                        help='chat connection sender port')
    parser.add_argument('-F', '--folder_logs', type=str,
                        default=os.getenv("FOLDER_LOGS"),
                        help='filepath of folder with chat history and logs')
    parser.add_argument('-L', '--logs', action='store_true',
                        default=True,
                        help='set logging')
    return parser

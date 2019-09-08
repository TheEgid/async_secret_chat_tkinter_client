import asyncio
import sys
import argparse
import os
from dotenv import load_dotenv

from services import install_logs_parameters
from services import set_and_check_connection
from services import broadcast_logger


async def broadcast_chat(host, port):
    reader, writer = await set_and_check_connection(host=host, port=port)
    try:
        while True:
            data = await reader.read(1024)
            msg = data.decode().rstrip()
            if msg:
                broadcast_logger.info(msg)
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        writer.close()


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


def main():
    load_dotenv()
    parser = get_args_parser()
    global args
    args = parser.parse_args()
    install_logs_parameters(args.folder_history, args.logs)
    try:
        listener = broadcast_chat(host=args.host, port=args.port_listener)
        asyncio.run(listener)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == '__main__':
    main()


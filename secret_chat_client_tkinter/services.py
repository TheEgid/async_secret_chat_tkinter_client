import os
import argparse
from tkinter import *

class ConnectionError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class AutorizationWindow:

    def __init__(self, master):
        name = StringVar()
        self.e = Entry(master, width=80, textvariable=name)
        self.b = Button(master, text="Зарегистрировать пользователя в чате")
        self.l = Label(master, bg='white', fg='black', width=80)
        self.e.pack()
        self.b.pack()
        self.l.pack()


    def get_val(self):

        self.b.bind()
        print(self.e.get())
        return self.e.get()

    # def setFunc(self, func):
    #     self.b['command'] = eval('self.' + func)
    # def strToSortlist(self):
    #     s = self.e.get()
    #     s = s.split()
    #     s.sort()
    #     self.l['text'] = ' '.join(s)
    # def strReverse(self):
    #     s = self.e.get()
    #     s = s.split()
    #     s.reverse()
    #     self.l['text'] = ' '.join(s)



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

    parser.add_argument('-F', '--folder_history', type=str,
                        default=os.getenv("FOLDER_HISTORY"),
                        help='filepath of chat history')

    parser.add_argument('-L', '--logs', action='store_true',
                        default=True,
                        help='set logging')
    return parser

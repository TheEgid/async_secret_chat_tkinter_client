from services import sanitize_message
from services import get_account_hash_and_nickname

from tkinter import Tk, Frame, Label, Button, Entry

global new_username
new_username = []


class RegistrationError(Exception):
    pass


class RegistrationFormDraw:
    def __init__(self):
        self.window = Tk()
        self.window.title('Minechat welcome!')
        self.window.geometry('700x200')
        self.window_frame = Frame()
        self.window_frame.pack()
        self.lbl = Label(self.window_frame, text="Введите имя")
        self.lbl.pack(pady=10)

        self.entry = Entry(width=70)
        self.entry.focus()
        self.entry.pack(pady=10)

        self.btn = Button(text="Зарегистрироваться")
        self.btn.pack(pady=10)
        self.btn.bind('<Button-1>', lambda event: self.callback())
        self.window.mainloop()

    def callback(self):
        new_username.append(sanitize_message(self.entry.get()))
        self.entry.forget()
        self.close()

    def close(self):
        self.window.destroy()
        self.window.quit()


def get_new_username():
    RegistrationFormDraw()
    if new_username:
        return new_username[0]
    else:
        raise RegistrationError


async def register(stream_for_write, new_name, attempts=5):
    reader, writer = stream_for_write
    hash_and_nickname = None
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

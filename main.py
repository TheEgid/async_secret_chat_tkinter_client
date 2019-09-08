import asyncio
import gui


messages_queue = asyncio.Queue()
sending_queue = asyncio.Queue()
status_updates_queue = asyncio.Queue()

async def submit_message():
    try:
        sending_queue.put_nowait('88')
        await sending_queue.get()

    finally:
        pass

loop = asyncio.get_event_loop()



messages_queue.put_nowait('Иван: Привет всем в этом чатике!')

# msg = await sending_queue.get()
# print(msg)  # Иван: Привет всем в этом чатике!

loop.run_until_complete(gui.draw(messages_queue, sending_queue, status_updates_queue))

event = gui.NicknameReceived('Василий Пупкин')
submit_message()
status_updates_queue.put_nowait(event)
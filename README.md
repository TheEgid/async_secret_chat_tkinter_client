# async_secret_chat_tkinter_client

Проект представляет собой учебный Async чат-клиент c графическим оконным интефейсом.
 
### Как установить

Скачиваем файлы. В папке secret_chat_client обязательно создаем .env файл. Ваш .env должен содержать строки:
```
HOST=хост_чата
PORT_LISTENER=порт_чата_для_получения_сообщений
PORT_SENDER=порт_чата_для_отправки_сообщений
LOGS_FOLDER=путь_для_папки_с_историей_и_логами
```
Python 3.7 должен быть уже установлен. Затем используйте pip для установки зависимостей:
```
pip install -r requirements.txt
```

### Использование
Из каталога с программой запускаeм.

```
python main.py
```
При первом запуске будет запущено диалоговое окно регистрации.

![reg](https://www.radikal.kz/images/2019/10/12/number1.jpg)

Полученный токен автоматически будет сохранен в .env файл для дальнейшей авторизации. 
 
Можно также запускать с аргументами, кроме текста сообщения аргументы имеют параметры по умолчанию из .env файла. 
 
 
usage: main.py [-h] [-H HOST] [-Pl PORT_LISTENER] [-Ps PORT_SENDER]
               [-F FOLDER_LOGS] [-L]

optional arguments:

-h, --help                                        **_show this help message and exit_**

-H HOST, --host HOST                              **_chat connection hostname (default: HOST)_**

-Pl PORT_LISTENER, --port_listener PORT_LISTENER  **_chat connection listener port (default: PORT_LISTENER)_**

-Ps PORT_SENDER, --port_sender PORT_SENDER        **_chat connection sender port (default: PORT_SENDER)_**

-F FOLDER_LOGS, --folder_logs FOLDER_LOGS         **_filepath of folder with chat history and logs (default: chat_logs)_**

-L, --logs                                        **_set logging (default: True)_**


![chat](https://www.radikal.kz/images/2019/10/12/number2.jpg)

### Особенности
Программа сохраняет логи работы и историю переписки в чате. Пр повторном запуске отображается история переписки в чате.

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).

'''
Бот для проверки доступных телефонных номеров и получения баланса счета.

Требуются следующие переменные окружения:
    - TOKEN_API
    - admin_id
    - url_sms_activate
    - url_api_sms
'''
import logging
import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv


class BotHandler:

    TOKEN_API = os.getenv('TOKEN_API')
    if TOKEN_API is None:
        raise ValueError("Переменная окружения 'TOKEN_API' не установлена")

    bot = Bot(TOKEN_API)
    dp = Dispatcher(storage=MemoryStorage())

    admin_id = os.getenv('admin_id')
    if admin_id is None:
        raise ValueError("Переменная окружения 'admin_id' не установлена")

    def __init__(self, bot: Bot, admin_id: int) -> None:
        self.bot = bot
        self.admin_id = admin_id
        self.stop = False

    async def start_command(self, message: types.Message) -> None:
        '''
        Обработчик команды /start.
        Отправляет ответ "Работаем" и запускает бесконечный цикл проверки
        доступных номеров.
        '''
        await message.answer(text="Работаем")
        asyncio.create_task(self.check_loop())

    async def check_command(self, message: types.Message) -> None:
        '''
        Обработчик команды /check.
        Вызывает функцию get_numbers для проверки доступных номеров.
        '''
        await self.get_numbers()

    async def balance_command(self, message: types.Message) -> None:
        '''
        Обработчик команды /balance.
        Вызывает функцию get_balance для проверки баланса счета.
        '''
        await self.get_balance()

    async def stop_command(self, message: types.Message) -> None:
        '''
        Обработчик команды /stop.
        Останавливает бесконечный цикл проверки доступных номеров и отправляет
        ответ "Остановлен".
        '''
        await message.answer("Остановлен")
        self.stop = True

    async def check_loop(self) -> None:
        '''
        Бесконечный цикл, который проверяет доступные телефонные номера
        каждые 10 минут (600 секунд).
        Если доступные номера найдены, он ожидает 30 минут (1800 секунд) перед
        следующей проверкой.
        '''
        while not self.stop:
            if await self.get_numbers():
                await asyncio.sleep(1800)
            await asyncio.sleep(600)

    async def get_numbers(self) -> bool:
        '''
        Отправляет GET-запрос к API SMS Activate для получения списка доступных
        телефонных номеров. Функция фильтрует результаты, чтобы включать только
        номера из страны 22 с ценой менее или равной 4.
        Если номера найдены, функция отправляет сообщение администратору с
        количеством и ценой номеров.
        '''
        try:
            url = os.getenv('url_sms_activate')
            if url is None:
                raise ValueError(
                    "Переменная окружения 'url_sms_activate' не установлена."
                    )
            headers = {
                'user-agent': (
                    'Mozilla/5.0 (iPad; CPU OS 16_3 like Mac OS X) '
                    'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                    'GSA/289.0.577695730 Mobile/15E148 Safari/604.1'
                    )
                }
            r = requests.get(url, headers=headers, timeout=10)
            print(r.text)
            json_data = r.json()
            # print(json_data)
            for value in json_data.values():
                if value.get("country") == 137 and value.get('price') <= 12:
                    count_numbers = value.get("count")
                    if count_numbers != 0:
                        message = (
                            f"Доступно {count_numbers} номеров по цене"
                            f" {value.get('price')}"
                        )
                        await self.send_message(message)
                        return True
        except Exception as e:
            # print(e)
            await self.send_message(f"Ошибка: {e}")
        await self.send_message("Нет доступных номеров")
        return False

    async def get_balance(self):
        '''
        Отправляет GET-запрос к API SMS Activate для получения баланса счета.
        Функция отправляет сообщение администратору с полученным балансом.
        '''
        try:
            url = os.getenv('url_api_sms')
            if url is None:
                raise ValueError(
                    "Переменная окружения 'url_api_sms' не установлена."
                    )
            r = requests.get(url, timeout=10)
            await self.send_message(f"Баланс: "
                                    f"{r.text.split('ACCESS_BALANCE:')[-1]}")
        except Exception as e:
            # print(e)
            await self.send_message(f"Ошибка: {e}")

    async def send_message(self, message: str) -> None:
        '''
        Отправляет сообщение администратору с указанным текстом.
        '''
        if self.admin_id is None:
            raise ValueError("Переменная окружения 'admin_id' не установлена")
        await bot.send_message(self.admin_id, message)

    async def on_startup(self):
        '''
        Функция, вызываемая при запуске бота.
        Устанавливает команды бота и запускает бесконечный цикл проверки
        доступных номеров.
        '''
        bot_commands = [
            BotCommand(command="/start", description="Запуск"),
            BotCommand(command="/check", description="Проверка номеров"),
            BotCommand(command="/balance", description="Проверка баланса"),
            BotCommand(command="/stop", description="Остановить работу")

        ]
        await self.bot.set_my_commands(bot_commands)
        asyncio.create_task(self.check_loop())

    async def main(self) -> None:
        """
        Запускает бота и начинает процесс опроса доступных номеров.
        """
        dp = Dispatcher(storage=MemoryStorage())
        dp.message.register(self.start_command,
                            Command(commands=['start']))
        dp.message.register(self.check_command,
                            Command(commands=['check']))
        dp.message.register(self.balance_command,
                            Command(commands=['balance']))
        dp.message.register(self.stop_command,
                            Command(commands=['stop']))
        await dp.start_polling(self.bot)


logging.basicConfig(level=logging.DEBUG,
                    filename='logs.log',
                    format='%(levelname)s (%(asctime)s): %(message)s '
                    '(Line: %(lineno)d) [%(filename)s]',
                    datefmt='%d/%m/%Y %I:%M:%S',
                    encoding='utf-8',
                    filemode='w')


if __name__ == '__main__':
    load_dotenv()
    TOKEN_API = os.getenv('TOKEN_API')
    admin_id = int(os.getenv('admin_id', 0))

    if TOKEN_API is None or admin_id == 0:
        raise ValueError("Переменные окружения 'TOKEN_API' и 'admin_id' должны"
                         "быть установлены")

    bot = Bot(TOKEN_API)
    bot_handler = BotHandler(bot, admin_id)
    asyncio.run(bot_handler.main())

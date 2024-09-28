'''
Бот для проверки доступных телефонных номеров и получения баланса счета.

Требуются следующие переменные окружения:
    - TOKEN_API
    - admin_id
    - url_sms_activate
    - url_api_sms
'''

import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv

load_dotenv()
TOKEN_API = os.getenv('TOKEN_API')
if TOKEN_API is None:
    raise ValueError("Переменная окружения 'TOKEN_API' не установлена")

bot = Bot(TOKEN_API)
dp = Dispatcher(storage=MemoryStorage())

admin_id = os.getenv('admin_id')
if admin_id is None:
    raise ValueError("Переменная окружения 'admin_id' не установлена")

STOP = False


async def check_loop() -> None:
    '''
    Бесконечный цикл, который проверяет доступные телефонные номера
    каждые 10 минут (600 секунд).
    Если доступные номера найдены, он ожидает 30 минут (1800 секунд) перед
    следующей проверкой.
    '''
    while True:
        if STOP:
            await asyncio.sleep(1)
            continue
        if await get_numbers():
            await asyncio.sleep(1800)
        await asyncio.sleep(600)


async def get_numbers() -> bool:
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
            'user-agent': ('Mozilla/5.0 (iPad; CPU OS 16_3 like Mac OS X) '
                           'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                           'GSA/289.0.577695730 Mobile/15E148 Safari/604.1')
            }
        r = requests.get(url, headers=headers, timeout=10)
        print(r.text)
        json_data = r.json()
        # print(json_data)
        for value in json_data.values():
            if value.get("country") == 22 and value.get('price') <= 4:
                count_numbers = value.get("count")
                if count_numbers != 0:
                    message = (
                        f"Доступно {count_numbers} номеров по цене"
                        f" {value.get('price')}"
                    )
                    await send_message(message)
                    return True
    except Exception as e:
        # print(e)
        await send_message(f"Ошибка: {e}")
    await send_message("Нет доступных номеров")
    return False


async def get_balance():
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
        await send_message(f"Баланс: {r.text.split('ACCESS_BALANCE:')[-1]}")
    except Exception as e:
        # print(e)
        await send_message(f"Ошибка: {e}")


async def send_message(message):
    '''
    Отправляет сообщение администратору с указанным текстом.
    '''
    if admin_id is None:
        raise ValueError("Переменная окружения 'admin_id' не установлена")
    await bot.send_message(admin_id, message)


@dp.message(Command(commands=['start']))
async def start_command(message: types.Message) -> None:
    '''
    Обработчик команды /start.
    Отправляет ответ "Работаем" и запускает бесконечный цикл проверки
    доступных номеров.
    '''
    global STOP
    await message.answer(text="Работаем")
    STOP = False
    asyncio.create_task(check_loop())


@dp.message(Command(commands=['check']))
async def check_command() -> None:
    '''
    Обработчик команды /check.
    Вызывает функцию get_numbers для проверки доступных номеров.
    '''
    await get_numbers()


@dp.message(Command(commands=['balance']))
async def balance_command() -> None:
    '''
    Обработчик команды /balance.
    Вызывает функцию get_balance для проверки баланса счета.
    '''
    await get_balance()


@dp.message(Command(commands=['stop']))
async def stop_command(message: types.Message) -> None:
    '''
    Обработчик команды /stop.
    Останавливает бесконечный цикл проверки доступных номеров и отправляет
    ответ "Остановлен".
    '''
    global STOP
    await message.answer("Остановлен")
    STOP = True


async def on_startup():
    '''
    Функция, вызываемая при запуске бота.
    Устанавливает команды бота и запускает бесконечный цикл проверки доступных
    номеров.
    '''
    bot_commands = [
        BotCommand(command="/start", description="Запуск"),
        BotCommand(command="/check", description="Проверка номеров"),
        BotCommand(command="/balance", description="Проверка баланса"),
        BotCommand(command="/stop", description="Остановить работу")

    ]
    await bot.set_my_commands(bot_commands)
    asyncio.create_task(check_loop())


async def main() -> None:
    """
    Запускает бота и начинает процесс опроса доступных номеров.
    """
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

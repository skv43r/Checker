from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.types import BotCommand
from dotenv import load_dotenv
import os

import requests
import asyncio


'''
Это Телеграм-бот, написанный на языке Python с использованием библиотеки aiogram. Бот предназначен для взаимодействия с API SMS Activate для проверки доступных телефонных номеров и получения баланса счета.
'''
load_dotenv()

TOKEN_API = os.getenv('TOKEN_API')
if TOKEN_API is None:
    raise ValueError("Переменная окружения 'TOKEN_API' не установлена")
bot = Bot(TOKEN_API)
dp = Dispatcher(bot)
admin_id = os.getenv('admin_id')
if admin_id is None:
    raise ValueError("Переменная окружения 'admin_id' не установлена")


'''Боту требуются следующие переменные среды для работы:

TOKEN_API: Токен API для Телеграм-бота
admin_id: ID администратора в Телеграме
url_sms_activate: URL API SMS Activate
url_api_sms: URL API SMS Activate для проверки баланса'''
STOP = False

async def check_loop() -> None:
    '''Бесконечный цикл, который проверяет доступные телефонные номера каждые 10 минут (600 секунд). Если доступные номера найдены, он ожидает 30 минут (1800 секунд) перед следующей проверкой.'''
    while True:
        global STOP
        if STOP:
            await asyncio.sleep(1)
            continue
        if await get_numbers():
            await asyncio.sleep(1800)
        await asyncio.sleep(600)

async def get_numbers() -> bool:
    '''Отправляет GET-запрос к API SMS Activate для получения списка доступных телефонных номеров. Функция фильтрует результаты, чтобы включать только номера из страны 22 с ценой менее или равной 4. Если номера найдены, функция отправляет сообщение администратору с количеством и ценой номеров.'''
    try:
        url = os.getenv('url_sms_activate')
        if url is None:
            raise ValueError("Переменная окружения 'url_sms_activate' не установлена")
        
        headers = {'user-agent':'Mozilla/5.0 (iPad; CPU OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/289.0.577695730 Mobile/15E148 Safari/604.1'}
        r = requests.get(url, headers=headers)
        print(r.text)
        json_data = r.json()
        # print(json_data)
        for key, i in json_data.items():
            if i.get("country") == 22 and i.get('price') <= 4:
                count_numbers = i.get("count")
                message = f"Доступно {count_numbers} номеров по цене {i.get('price')}"
                await send_message(message)
                return True
    except Exception as e:
        # print(e)
        await send_message(f"Ошибка: {e}")
    await send_message(f"Нет доступных номеров")
    return False

async def get_balance():
    '''Отправляет GET-запрос к API SMS Activate для получения баланса счета. Функция отправляет сообщение администратору с полученным балансом.'''
    try:
        url = os.getenv('url_api_sms')
        if url is None:
            raise ValueError("Переменная окружения 'url_api_sms' не установлена")
        
        r = requests.get(url)
        await send_message(f"Баланс: {r.text.split('ACCESS_BALANCE:')[-1]}")
    except Exception as e:
        # print(e)
        await send_message(f"Ошибка: {e}")


async def send_message(message):
    '''Отправляет сообщение администратору с указанным текстом.'''
    global admin_id
    global bot
    if admin_id is None:
        raise ValueError("Переменная окружения 'admin_id' не установлена")
    await bot.send_message(admin_id, message)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message) -> None:
    '''Обработчик команды /start. Отправляет ответ "Работаем" и запускает бесконечный цикл проверки доступных номеров.'''
    global STOP
    await message.answer(text="Работаем")
    STOP = False

@dp.message_handler(commands=['check'])
async def check_command(message: types.Message) -> None:
    '''Обработчик команды /check. Вызывает функцию get_numbers для проверки доступных номеров.'''
    await get_numbers()

@dp.message_handler(commands=['balance'])
async def balance_command(message: types.Message) -> None:
    '''Обработчик команды /balance. Вызывает функцию get_balance для проверки баланса счета.'''
    await get_balance()

@dp.message_handler(commands=['stop'])
async def stop_command(message: types.Message) -> None:
    '''Обработчик команды /stop. Останавливает бесконечный цикл проверки доступных номеров и отправляет ответ "Остановлен".'''
    global STOP
    await message.answer("Остановлен")
    STOP = True

async def on_startup(x):
    '''Функция, вызываемая при запуске бота. Устанавливает команды бота и запускает бесконечный цикл проверки доступных номеров.'''
    bot_commands = [
        BotCommand(command="/start", description="Запуск"),
        BotCommand(command="/check", description="Проверка номеров"),
        BotCommand(command="/balance", description="Проверка баланса"),
        BotCommand(command="/stop", description="Остановить работу")

    ]
    global bot
    await bot.set_my_commands(bot_commands)
    asyncio.create_task(check_loop())

if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           on_startup=on_startup,
                           skip_updates=True)
    asyncio.create_task(get_numbers())
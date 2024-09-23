from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.types import BotCommand
from dotenv import load_dotenv
import os

import requests
import asyncio

load_dotenv()

TOKEN_API = os.getenv('TOKEN_API')
bot = Bot(TOKEN_API)
dp = Dispatcher(bot)
admin_id = os.getenv('admin_id')
STOP = False

async def check_loop():
    while True:
        global STOP
        if STOP:
            await asyncio.sleep(1)
            continue
        if await get_numbers():
            await asyncio.sleep(1800)
        await asyncio.sleep(600)

async def get_numbers():
    try:
        url = os.getenv('url_sms_activate')
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
    try:
        url = os.getenv('url_api_sms')
        r = requests.get(url)
        await send_message(f"Баланс: {r.text.split('ACCESS_BALANCE:')[-1]}")
    except Exception as e:
        # print(e)
        await send_message(f"Ошибка: {e}")


async def send_message(message):
    global admin_id
    global bot
    await bot.send_message(admin_id, message)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    global STOP
    await message.answer(text="Работаем")
    STOP = False

@dp.message_handler(commands=['check'])
async def start_command(message: types.Message):
    await get_numbers()

@dp.message_handler(commands=['balance'])
async def start_command(message: types.Message):
    await get_balance()

@dp.message_handler(commands=['stop'])
async def start_command(message: types.Message):
    global STOP
    await message.answer("Остановлен")
    STOP = True

async def on_startup(x):
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
    asyncio.create_task(get_numbers)


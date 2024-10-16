"""
Этот модуль реализует Telegram-бота,
который взаимодействует с сервисом проверки номеров и отправки SMS.

Импортируемые библиотеки:
- os: для работы с переменными окружения.
- asyncio: для асинхронного программирования.
- logging: для ведения логов.
- aiogram: библиотека для работы с Telegram Bot API.
- dotenv: для загрузки переменных окружения из файла .env.
- checker_solid: пользовательские классы для обработки логики бота.

Основные функции:
- load_config: загружает конфигурацию из переменных окружения.
- main: основной асинхронный метод, который инициализирует бота и
        запускает процесс опроса доступных номеров.

Классы:
- BotHandler: класс для обработки команд бота.
- SmsService: класс для работы с сервисом отправки SMS.
- NumberChecker: класс для проверки доступных номеров.

Команды бота:
- /start: запускает бота.
- /check: проверяет доступные номера.
- /balance: отображает баланс.
- /stop: останавливает бота.
"""
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from checker_solid import BotHandler, SmsService, NumberChecker


def load_config() -> tuple[str, int, str, str]:
    """Загружает конфигурацию из переменных окружения."""
    load_dotenv()
    token = os.getenv('TOKEN_API')
    admin_id = os.getenv('admin_id')
    url_sms_activate = os.getenv('url_sms_activate')
    url_api_sms = os.getenv('url_api_sms')

    if (token is None
            or admin_id is None
            or url_sms_activate is None
            or url_api_sms is None):
        raise ValueError("Одна из переменных окружения имеет значение None")

    return token, int(admin_id), url_sms_activate, url_api_sms


async def main() -> None:
    """Запускает бота и начинает процесс опроса доступных номеров."""
    token, admin_id, url_sms_activate, url_api_sms = load_config()

    bot = Bot(token=token)
    sms_service = SmsService(admin_id)
    number_checker = NumberChecker(sms_service, url_sms_activate, url_api_sms)
    handler = BotHandler(bot, admin_id, sms_service, number_checker)

    dp = Dispatcher(storage=MemoryStorage())
    dp.message.register(handler.start_command,
                        Command(commands=['start']))
    dp.message.register(handler.check_command,
                        Command(commands=['check']))
    dp.message.register(handler.balance_command,
                        Command(commands=['balance']))
    dp.message.register(handler.stop_command,
                        Command(commands=['stop']))

    await dp.start_polling(handler.bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        filename='logs.log',
                        format='%(levelname)s (%(asctime)s): %(message)s '
                        '(Line: %(lineno)d) [%(filename)s]',
                        datefmt='%d/%m/%Y %I:%M:%S',
                        encoding='utf-8',
                        filemode='w')
    asyncio.run(main())

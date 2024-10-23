"""
Этот модуль реализует Telegram-бота,
который взаимодействует с сервисом проверки номеров и отправки SMS.

Импортируемые библиотеки:
- asyncio: для асинхронного программирования.
- logging: для ведения логов.
- aiogram: библиотека для работы с Telegram Bot API.

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
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from sms_service import SmsService
from number_checker import NumberChecker
from bot_handler import BotHandler
from config import Settings


def load_config() -> Settings:
    """Загружает конфигурацию из переменных окружения."""
    return Settings() # type: ignore


async def main() -> None:
    """Запускает бота и начинает процесс опроса доступных номеров."""
    settings = load_config()
    if not all([settings.token,
                settings.admin_id,
                settings.url_sms_activate,
                settings.url_api_sms]):
        raise ValueError("Отсутствуют обязательные параметры конфигурации.")

    bot = Bot(token=settings.token)
    sms_service = SmsService(settings.admin_id)
    number_checker = NumberChecker(sms_service,
                                   settings.url_sms_activate,
                                   settings.url_api_sms)
    handler = BotHandler(bot, settings.admin_id, sms_service, number_checker)

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

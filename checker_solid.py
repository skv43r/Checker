'''
Бот для проверки доступных телефонных номеров и получения баланса счета.

Требуются следующие переменные окружения:
    - TOKEN_API
    - admin_id
    - url_sms_activate
    - url_api_sms
'''
import asyncio
import requests
from aiogram import Bot, types
from aiogram.types import BotCommand


class SmsService:
    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    async def send_message(self, bot: Bot, message: str) -> None:
        '''
        Отправляет сообщение администратору с указанным текстом.
        '''
        await bot.send_message(self.admin_id, message)


class NumberChecker:
    def __init__(self,
                 sms_service: SmsService,
                 url_sms_activate: str,
                 url_api_sms: str):
        self.sms_service = sms_service
        self.url_sms_activate = url_sms_activate
        self.url_api_sms = url_api_sms

    async def get_numbers(self, bot: Bot) -> bool:
        '''
        Отправляет GET-запрос к API SMS Activate для получения списка доступных
        телефонных номеров. Функция фильтрует результаты, чтобы включать только
        номера из страны 22 с ценой менее или равной 4.
        Если номера найдены, функция отправляет сообщение администратору с
        количеством и ценой номеров.
        '''
        try:
            headers = {
                'user-agent': (
                    'Mozilla/5.0 (iPad; CPU OS 16_3 like Mac OS X) '
                    'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                    'GSA/289.0.577695730 Mobile/15E148 Safari/604.1'
                )
            }
            r = requests.get(self.url_sms_activate,
                             headers=headers,
                             timeout=10)
            r.raise_for_status()
            json_data = r.json()
            for value in json_data.values():
                if value.get("country") == 137 and value.get('price') <= 12:
                    count_numbers = value.get("count")
                    if count_numbers != 0:
                        message = (
                            f"Доступно {count_numbers} номеров по "
                            f"цене {value.get('price')}"
                        )
                        await self.sms_service.send_message(bot, message)
                        return True
        except requests.RequestException as e:
            await self.sms_service.send_message(bot, f"Ошибка запроса: {e}")
        except ValueError as e:
            await self.sms_service.send_message(bot, f"Ошибка обработки "
                                                f"данных: {e}")
        await self.sms_service.send_message(bot, "Нет доступных номеров")
        return False

    async def get_balance(self, bot: Bot) -> None:
        '''
        Отправляет GET-запрос к API SMS Activate для получения баланса счета.
        Функция отправляет сообщение администратору с полученным балансом.
        '''
        try:
            r = requests.get(self.url_api_sms, timeout=10)
            r.raise_for_status()
            balance = r.text.split('ACCESS_BALANCE:')[-1]
            await self.sms_service.send_message(bot, f"Баланс: {balance}")
        except requests.RequestException as e:
            await self.sms_service.send_message(bot, f"Ошибка запроса: {e}")
        except Exception as e:
            await self.sms_service.send_message(bot, f"Ошибка: {e}")


class BotHandler:
    def __init__(self,
                 bot: Bot,
                 admin_id: int,
                 sms_service: SmsService,
                 number_checker: NumberChecker) -> None:
        self.bot = bot
        self.admin_id = admin_id
        self.stop = False
        self.sms_service = sms_service
        self.number_checker = number_checker

    async def start_command(self, message: types.Message) -> None:
        '''
        Обработчик команды /start.
        Отправляет ответ "Работаем" и запускает бесконечный цикл проверки
        доступных номеров.
        '''
        await message.answer(text="Работаем")
        if not hasattr(self, 'check_loop_task') or self.check_loop_task.done():
            self.check_loop_task = asyncio.create_task(self.check_loop())

    async def check_command(self, message: types.Message) -> None:
        '''
        Обработчик команды /check.
        Вызывает функцию get_numbers для проверки доступных номеров.
        '''
        await self.number_checker.get_numbers(self.bot)

    async def balance_command(self, message: types.Message) -> None:
        '''
        Обработчик команды /balance.
        Вызывает функцию get_balance для проверки баланса счета.
        '''
        await self.number_checker.get_balance(self.bot)

    async def stop_command(self, message: types.Message) -> None:
        '''
        Обработчик команды /stop.
        Останавливает бесконечный цикл проверки доступных номеров и отправляет
        ответ "Остановлен".
        '''
        await message.answer("Остановлен")
        self.stop = True
        if hasattr(self, 'check_loop_task'):
            self.check_loop_task.cancel()

    async def check_loop(self) -> None:
        '''
        Бесконечный цикл, который проверяет доступные телефонные номера
        каждые 10 минут (600 секунд).
        Если доступные номера найдены, он ожидает 30 минут (1800 секунд) перед
        следующей проверкой.
        '''
        self.stop = False
        while not self.stop:
            if await self.number_checker.get_numbers(self.bot):
                await asyncio.sleep(1800)
            await asyncio.sleep(600)

    async def on_startup(self) -> None:
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

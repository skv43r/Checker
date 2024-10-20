import asyncio
from aiogram import Bot, types
from aiogram.types import BotCommand
from sms_service import SmsService
from number_checker import NumberChecker


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

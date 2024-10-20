from aiogram import Bot


class SmsService:
    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    async def send_message(self, bot: Bot, message: str) -> None:
        '''
        Отправляет сообщение администратору с указанным текстом.
        '''
        await bot.send_message(self.admin_id, message)

import aiohttp
import asyncio
from aiogram import Bot
from sms_service import SmsService
from aiohttp import ClientTimeout

class NumberChecker:
    def __init__(self,
                 sms_service: SmsService,
                 url_sms_activate: str,
                 url_api_sms: str):
        self.sms_service = sms_service
        self.url_sms_activate = url_sms_activate
        self.url_api_sms = url_api_sms

    async def fetch(self, session, url):
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def get_numbers(self, bot: Bot) -> bool:
        '''
        Отправляет GET-запрос к API SMS Activate для получения списка доступных
        телефонных номеров. Функция фильтрует результаты, чтобы включать только
        номера из страны 22 с ценой менее или равной 4.
        Если номера найдены, функция отправляет сообщение администратору с
        количеством и ценой номеров.
        '''
        async with aiohttp.ClientSession() as session:
            try:
                json_data = await self.fetch(session, self.url_sms_activate)

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
            except aiohttp.ClientConnectionError:
                await self.sms_service.send_message(bot, "Нет соединения с API")
            except asyncio.TimeoutError:
                await self.sms_service.send_message(bot, "Время ожидания истекло")
            except aiohttp.ClientResponseError as e:
                await self.sms_service.send_message(bot, f"Ошибка запроса: {e}")
            except ValueError as e:
                await self.sms_service.send_message(bot, f"Ошибка обработки "
                                                         f"данных: {e}")
            except Exception as e:
                await self.sms_service.send_message(bot, f"Неожиданная ошибка: {e}")

        await self.sms_service.send_message(bot, "Нет доступных номеров")
        return False

    async def get_balance(self, bot: Bot) -> None:
        '''
        Отправляет GET-запрос к API SMS Activate для получения баланса счета.
        Функция отправляет сообщение администратору с полученным балансом.
        '''
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(self.url_api_sms, timeout=ClientTimeout(total=10))
                response.raise_for_status()
                balance = response.text.split('ACCESS_BALANCE:')[-1]
                await self.sms_service.send_message(bot, f"Баланс: {balance}")
            except aiohttp.ClientConnectionError:
                await self.sms_service.send_message(bot, "Нет соединения с API")
            except asyncio.TimeoutError:
                await self.sms_service.send_message(bot, "Время ожидания истекло")
            except aiohttp.ClientResponseError as e:
                await self.sms_service.send_message(bot, f"Ошибка запроса: {e}")
            except Exception as e:
                await self.sms_service.send_message(bot, f"Неожиданная ошибка: {e}")

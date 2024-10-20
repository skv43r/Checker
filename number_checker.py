import aiohttp
import asyncio
import json
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
                response = await session.get(self.url_sms_activate)
                response.raise_for_status()
                try:
                    json_data = await response.json()
                except aiohttp.ContentTypeError:
                    text_data = await response.text()
                    try:
                        json_data = json.loads(text_data)
                    except ValueError:
                        await self.sms_service.send_message(
                            bot,
                            f"Невозможно обработать ответ: {text_data}"
                            )
                        return False

                for value in json_data.values():
                    if value.get("country") == 137 and value.get('price') <= 9:
                        count_numbers = value.get("count")
                        if count_numbers != 0:
                            message = (
                                f"Доступно {count_numbers} номеров по "
                                f"цене {value.get('price')}"
                            )
                            await self.sms_service.send_message(bot, message)
                            return True

            except aiohttp.ClientConnectionError:
                await self.sms_service.send_message(bot,
                                                    "Нет соединения с API")
            except asyncio.TimeoutError:
                await self.sms_service.send_message(bot,
                                                    "Время ожидания истекло")
            except aiohttp.ClientResponseError as e:
                await self.sms_service.send_message(bot,
                                                    f"Ошибка запроса: {e}")
            except ValueError as e:
                await self.sms_service.send_message(bot, f"Ошибка обработки "
                                                         f"данных: {e}")
            except Exception as e:
                await self.sms_service.send_message(bot,
                                                    f"Неожиданная ошибка: {e}")

        await self.sms_service.send_message(bot, "Нет доступных номеров")
        return False

    async def get_balance(self, bot: Bot) -> None:
        '''
        Отправляет GET-запрос к API SMS Activate для получения баланса счета.
        Функция отправляет сообщение администратору с полученным балансом.
        '''
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(self.url_api_sms,
                                             timeout=ClientTimeout(total=10))
                response.raise_for_status()
                text = await response.text()
                balance = text.split('ACCESS_BALANCE:')[-1]
                await self.sms_service.send_message(bot,
                                                    f"Баланс: {balance}")
            except aiohttp.ClientConnectionError:
                await self.sms_service.send_message(bot,
                                                    "Нет соединения с API")
            except asyncio.TimeoutError:
                await self.sms_service.send_message(bot,
                                                    "Время ожидания истекло")
            except aiohttp.ClientResponseError as e:
                await self.sms_service.send_message(bot,
                                                    f"Ошибка запроса: {e}")
            except Exception as e:
                await self.sms_service.send_message(bot,
                                                    f"Неожиданная ошибка: {e}")

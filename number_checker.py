import requests
from aiogram import Bot
from sms_service import SmsService

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

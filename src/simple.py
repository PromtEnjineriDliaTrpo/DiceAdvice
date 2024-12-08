import json
import random

from mistralai import Mistral
from telebot import types

api_key = '3Hc4mDWfCKf0H6H3MJDwxCcHX8HpZA4d'

def _is_yes_no_question(question, api_key):
    with Mistral(
        api_key=api_key,
    ) as s:
        res = s.chat.complete(model="mistral-large-latest", messages=[
            {
                "role": "system",
                "content": "You are an assistant that determines if a question can be answered with 'yes' or 'no'. Respond only with 'True' if it's a yes/no question, or 'False' if it's not."
            },
            {
                "role": "user",
                "content": f"Is this a yes/no question: '{question}'? Respond only with True or False."
            },
        ])

        if res is not None:
            print(res.json())
            js = json.loads(res.json())
            result = js['choices'][0]['message']['content'].strip().lower()
            return result[0:4] == "true"


def handle_simple_q(question, api_token):
    if not _is_yes_no_question(question, api_token):
        return "Некорректный вопрос"
    else:
        prob = random.randint(0, 1)
        if prob == 1:
            return f'Вопрос: {question}\nОтвет: Да'
        else:
            return f'Вопрос: {question}\nОтвет: No'


# Функция для создания меню простого модуля
def simple_module_menu():
    markup = types.InlineKeyboardMarkup()
    back_button = types.InlineKeyboardButton("Вернуться назад", callback_data='back_to_main')
    markup.add(back_button)
    return markup


# Функция для создания меню после ответа
def simple_module_after_response_menu():
    markup = types.InlineKeyboardMarkup()
    back_button = types.InlineKeyboardButton("Вернуться назад", callback_data='back_to_main')
    markup.add(back_button)
    return markup

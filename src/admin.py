import json
from tabulate import tabulate
import telebot

from telebot import types


ADMIN_IDS = [
    406136592,
    1230349081,
]


def get_feedback():
    with open('../admin/feedback.json', 'r') as f:
        data = json.load(f)

    table_data = []
    for user_id, reviews in list(data.items())[:5]:  # берем первых 5 пользователей
        for review in reviews[:5]:  # берем первые 5 отзывов
            table_data.append({
                'user_id': user_id,
                'review': review
            })

    # Выводим таблицу
    return tabulate(table_data, headers="keys", tablefmt="grid")


def is_admin(user_id):
    print(user_id)
    return user_id in ADMIN_IDS


def admin_module_menu():
    markup = types.InlineKeyboardMarkup()
    stat_btn = types.InlineKeyboardButton("Показать статистику", callback_data='show_statistic')
    reviews_btn = types.InlineKeyboardButton("Показать отзывы", callback_data='show_reviews')
    back_btn = types.InlineKeyboardButton("Назад", callback_data='back_to_main')
    markup.add(stat_btn)
    markup.add(reviews_btn)
    markup.add(back_btn)
    return markup

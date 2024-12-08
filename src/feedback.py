import json

from telebot import types


# Функция для создания меню простого модуля
def feedback_module_menu():
    markup = types.InlineKeyboardMarkup()
    back_button = types.InlineKeyboardButton("Вернуться назад", callback_data='back_to_main')
    markup.add(back_button)
    return markup

def handle_user_feedback(user_id, user_message):
    with open('../admin/feedback.json', 'r+') as file:
        data = json.load(file)

        user_id = str(user_id)

        if user_id not in data:
            data[user_id] = [user_message]
        else:
            data[user_id].append(user_message)
        file.seek(0)
        json.dump(data, file)
        file.truncate()
        file.close()

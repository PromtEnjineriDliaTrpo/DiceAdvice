import configparser
import json
import os
import requests
import telebot

from tabulate import tabulate
from telebot import types

#import modules
from admin import (
    admin_module_menu,
    get_feedback,
    is_admin,
)
from complex import (
    complex_module_menu,
    handle_complex_question,
    mode_selection_menu,
)
from feedback import (
    handle_user_feedback,
    feedback_module_menu,
)
from simple import (
    handle_simple_q,
    simple_module_menu,
    simple_module_after_response_menu,
)
from stats import (
    get_stat,
    increase_stat,
    COMPLEX_MODULE_STATS,
    SIMPLE_MODULE_STATS,
    TIP_OF_THE_DAY_STATS,
)
from totd import (
    get_random_quote,
)

CONFIG = configparser.ConfigParser()
CONFIG.read(f'{os.path.dirname(os.path.abspath(__file__))}/../configs/config.ini')

hugging_face_token = CONFIG['HUGGING_FACE_API']['hugging_face_token']
token = CONFIG['BOT.TELEGRAM']['token']
mistral_token = CONFIG['BOT.MISTRAL']['token']

bot = telebot.TeleBot(token)

user_states = {}
user_menu_messages = {}

# Константы состояний
STATE_AWAITING_SIMPLE_QUESTION = "awaiting_simple_question"
STATE_SELECTING_COMPLEX_OPTION = "selecting_complex_option"
STATE_AWAITING_COMPLEX_QUESTION = "awaiting_complex_question"
STATE_IN_MAIN_MENU = "in_main_menu"
STATE_SELECTING_adminOPTION = "selecting_admin_option"
STATE_DEFAULT = "default"
STATE_AWAITING_FEEDBACk = 'awaiting_feedback'

user_complex_preferences = {}


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = main_menu(message.from_user.id)
    sent_message = bot.send_message(message.chat.id, "Добро пожаловать! Выберите опцию:", reply_markup=markup)
    # Сохраняем идентификатор отправленного сообщения с меню
    user_menu_messages[message.from_user.id] = sent_message.message_id
    user_states[message.from_user.id] = STATE_DEFAULT


# Функция для создания главного меню
def main_menu(user_id=0):
    markup = types.InlineKeyboardMarkup()
    button_simple = types.InlineKeyboardButton("1 - Simple module", callback_data='simple_module')
    button_complex = types.InlineKeyboardButton("2 - Complex module", callback_data='complex_module')
    button_admin = types.InlineKeyboardButton("3 - Admin module", callback_data='admin_module')
    button_feedback = types.InlineKeyboardButton("4 - Feedback module", callback_data='feedback_module')
    button_tip = types.InlineKeyboardButton("5 - Tip of the day", callback_data='tip_of_the_day')
    markup.add(button_simple)
    markup.add(button_complex)
    if is_admin(user_id):
        markup.add(button_admin)
    markup.add(button_feedback)
    markup.add(button_tip)
    return markup


# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == 'tip_of_the_day':
        bot.answer_callback_query(call.id)
        delete_previous_menu(user_id, chat_id)
        bot.send_message(chat_id, get_random_quote())
        markup = main_menu(user_id)
        increase_stat(TIP_OF_THE_DAY_STATS)
        sent_message = bot.send_message(chat_id, "Welcome! Choose the option:", reply_markup=markup)
        # Сохраняем идентификатор отправленного сообщения с меню
        user_menu_messages[user_id] = sent_message.message_id
        user_states[user_id] = STATE_DEFAULT

    elif call.data == 'simple_module':
        # Устанавливаем состояние пользователя
        user_states[user_id] = STATE_AWAITING_SIMPLE_QUESTION
        markup = simple_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Hi, u've chosen simple module, write ur question:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id

    elif call.data == 'complex_module':
        # New complex module logic
        user_states[user_id] = STATE_SELECTING_COMPLEX_OPTION
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="U've chosen cmplex module. Choose parameters or ask the question:",
                              reply_markup=markup)

    elif call.data == 'select_mode':
        # Display the mode selection menu
        user_states[user_id] = STATE_SELECTING_COMPLEX_OPTION
        markup = mode_selection_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="choose mode for the AI:", reply_markup=markup)

    elif call.data.startswith('set_mode_'):
        # Set the selected mode for the user
        mode = call.data.split('_')[-1]
        user_complex_preferences[user_id] = user_complex_preferences.get(user_id, {})
        user_complex_preferences[user_id]['mode'] = mode
        bot.answer_callback_query(call.id, f"Mode installed: {mode.capitalize()}")
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text=f"U've choosen: {mode.capitalize()}. Now u can ask the question.",
                              reply_markup=markup)

    elif call.data == 'include_datetime':
        # Toggle datetime inclusion for the user
        user_complex_preferences[user_id] = user_complex_preferences.get(user_id, {})
        current_pref = user_complex_preferences[user_id].get('include_datetime', False)
        user_complex_preferences[user_id]['include_datetime'] = not current_pref
        status = "On" if not current_pref else "Off"
        bot.answer_callback_query(call.id, f"Add current datetime {status}.")
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text=f"Add current datetime {status}. Now u can ask the question.",
                              reply_markup=markup)

    elif call.data == 'cancel_mode':
        # Cancel the selected mode
        user_complex_preferences[user_id] = user_complex_preferences.get(user_id, {})
        if 'mode' in user_complex_preferences[user_id]:
            del user_complex_preferences[user_id]['mode']
            bot.answer_callback_query(call.id, "The mode is reset.")
        else:
            bot.answer_callback_query(call.id, "The mode is no longer set.")
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="The mode is reset. Select the options or ask a question.", reply_markup=markup)

    elif call.data == 'cancel_datetime':
        # Cancel datetime inclusion
        user_complex_preferences[user_id] = user_complex_preferences.get(user_id, {})
        if user_complex_preferences[user_id].get('include_datetime', False):
            user_complex_preferences[user_id]['include_datetime'] = False
            bot.answer_callback_query(call.id, "Adding the current day and time is disabled.")
        else:
            bot.answer_callback_query(call.id, "Adding the current day and time is already disabled.")
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Adding the current day and time is disabled. Select the options or ask a question.",
                              reply_markup=markup)

    elif call.data == 'ask_complex_question':
        # Prompt the user to send their question
        user_states[user_id] = STATE_AWAITING_COMPLEX_QUESTION
        back_button = types.InlineKeyboardMarkup()
        back_button.add(types.InlineKeyboardButton("Go back", callback_data='complex_module'))
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Enter your question for a complex module:", reply_markup=back_button)

    elif call.data == 'back_to_main':
        # Сбрасываем состояние пользователя
        user_states[user_id] = STATE_DEFAULT
        markup = main_menu(user_id)

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="You are back in the main menu. Select an option:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id

    elif call.data == 'ask_another_question':
        # Пользователь хочет задать еще вопрос
        user_states[user_id] = STATE_AWAITING_SIMPLE_QUESTION
        markup = simple_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Write the following question:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id
    elif call.data == 'admin_module':
        # Устанавливаем состояние пользователя
        user_states[user_id] = STATE_AWAITING_SIMPLE_QUESTION
        markup = admin_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                            text="Hello, my dear and esteemed admin, select the option:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id
    elif call.data == 'show_statistic':
        bot.answer_callback_query(call.id)
        delete_previous_menu(user_id, chat_id)
        bot.send_message(chat_id, get_stat())

        # Устанавливаем состояние пользователя
        user_states[user_id] = STATE_DEFAULT
        markup = admin_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.send_message(chat_id=chat_id,
                            text="Hello, my dear and esteemed admin, select the option:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id
    elif call.data == 'show_reviews':
        bot.answer_callback_query(call.id)
        delete_previous_menu(user_id, chat_id)
        with open('../admin/feedback.json', 'rb') as f:
            bot.send_document(chat_id, f)
        bot.send_message(chat_id, get_feedback())

        # Устанавливаем состояние пользователя
        user_states[user_id] = STATE_DEFAULT
        markup = admin_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.send_message(chat_id=chat_id,
                            text="Hello, my dear and esteemed admin, select the option:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id
    elif call.data == 'feedback_module':
        # Устанавливаем состояние пользователя
        user_states[user_id] = STATE_AWAITING_FEEDBACk
        markup = feedback_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Hello, my inexpensive and slightly respected user, write a review:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id
    else:
        # Обработка других модулей (пока не реализованы)
        bot.answer_callback_query(call.id)
        delete_previous_menu(user_id, chat_id)
        bot.send_message(chat_id, "This module is still in development.")
        markup = main_menu(user_id)
        sent_message = bot.send_message(chat_id, "Welcome! Select an option:", reply_markup=markup)
        # Сохраняем идентификатор отправленного сообщения с меню
        user_menu_messages[user_id] = sent_message.message_id
        user_states[user_id] = STATE_DEFAULT


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in user_states:
        state = user_states[user_id]
        if state == STATE_AWAITING_SIMPLE_QUESTION:
            # Пользователь отправил вопрос в простом модуле
            # Здесь можно обработать вопрос, если нужно

            # Перед отправкой нового сообщения удаляем предыдущее меню
            delete_previous_menu(user_id, chat_id)

            msg_text = message.text

            markup = simple_module_after_response_menu()

            msg = handle_simple_q(msg_text, mistral_token)
            bot.send_message(chat_id, msg)

            sent_message = bot.send_message(chat_id, "Ask me again.", reply_markup=markup)
            # Сохраняем идентификатор отправленного сообщения с меню
            user_menu_messages[user_id] = sent_message.message_id
            # Остаемся в текущем состоянии или сбрасываем, если нужно
            # user_states[user_id] = STATE_DEFAULT
            increase_stat(SIMPLE_MODULE_STATS)
        elif state == STATE_AWAITING_COMPLEX_QUESTION:
            delete_previous_menu(user_id, chat_id)
            user_message = message.text
            preferences = user_complex_preferences.get(user_id, {})
            mode = preferences.get('mode')
            include_datetime = preferences.get('include_datetime', False)
            msg_ = handle_complex_question(chat_id, hugging_face_token, user_message, mode, include_datetime)
            bot.send_message(chat_id, msg_)
            user_states[user_id] = STATE_SELECTING_COMPLEX_OPTION
            bot.send_message(chat_id, "You can ask the following question or return to the menu.",
                             reply_markup=complex_module_menu())
            increase_stat(COMPLEX_MODULE_STATS)
        elif state == STATE_AWAITING_FEEDBACk:
            delete_previous_menu(user_id, chat_id)
            user_message = message.text

            handle_user_feedback(user_id, user_message)

            user_states[user_id] = STATE_AWAITING_FEEDBACk
            sent_message = bot.send_message(chat_id, "You can write the following review or return to the menu.",
                             reply_markup=feedback_module_menu())
            user_menu_messages[user_id] = sent_message.message_id
        else:
            # Если состояние другое, игнорируем или отправляем сообщение
            bot.send_message(chat_id, "Please select an option from the menu.")
    else:
        # Если состояние не установлено, просим выбрать опцию из меню
        bot.send_message(chat_id, "Please select an option from the menu using the command /start.")


# Функция для удаления предыдущего сообщения с меню
def delete_previous_menu(user_id, chat_id):
    if user_id in user_menu_messages:
        message_id = user_menu_messages[user_id]
        try:
            bot.delete_message(chat_id, message_id)
            # Удаляем запись из словаря после удаления сообщения
            del user_menu_messages[user_id]
        except:
            pass  # Игнорируем ошибки, если сообщение нельзя удалить или оно уже удалено


# Запуск бота
bot.polling()

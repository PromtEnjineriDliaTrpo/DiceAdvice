import telebot
from telebot import types
import configparser
import datetime
import requests
from hugging_face_model import generate_response
import json
from tabulate import tabulate

#import modules
from feedback import (
    handle_user_feedback,
    feedback_module_menu,
)
from simple import (
    handle_simple_q,
    simple_module_menu,
    simple_module_after_response_menu,
)

CONFIG = configparser.ConfigParser()
CONFIG.read('../configs/config.ini')

hugging_face_token = CONFIG['HUGGING_FACE_API']['hugging_face_token']
token = CONFIG['BOT.TELEGRAM']['token']
mistral_token = CONFIG['BOT.MISTRAL']['token']


admin_ids = [
    406136592,
    1230349081
]

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

SIMPLE_MODULE_STATS = 'simple_module_stats'
COMPLEX_MODULE_STATS = 'complex_module_stats'
TIP_OF_THE_DAY_STATS = 'tip_of_the_day_stats'

complex_modes = {
    "philosopher": "Respond as a wise philosopher.",
    "politician": "Respond like a professional politician.",
    "teacher": "Respond like an experienced teacher."
}

user_complex_preferences = {}

# Fallback Quotes (in case API fails)
FALLBACK_QUOTES = [
    "“The only limit to our realization of tomorrow is our doubts of today.” – Franklin D. Roosevelt",
    "“In the middle of every difficulty lies opportunity.” – Albert Einstein",
    "“Success is not final, failure is not fatal: It is the courage to continue that counts.” – Winston Churchill",
    "“Happiness is not something ready-made. It comes from your own actions.” – Dalai Lama",
    "“Your time is limited, don’t waste it living someone else’s life.” – Steve Jobs",
    "“Life is what happens when you’re busy making other plans.” – John Lennon"
]


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = main_menu()
    sent_message = bot.send_message(message.chat.id, "Добро пожаловать! Выберите опцию:", reply_markup=markup)
    # Сохраняем идентификатор отправленного сообщения с меню
    user_menu_messages[message.from_user.id] = sent_message.message_id
    user_states[message.from_user.id] = STATE_DEFAULT


# Функция для создания главного меню
def main_menu():
    markup = types.InlineKeyboardMarkup()
    button_simple = types.InlineKeyboardButton("1 - Простой модуль", callback_data='simple_module')
    button_complex = types.InlineKeyboardButton("2 - Сложный модуль", callback_data='complex_module')
    button_admin = types.InlineKeyboardButton("3 - Модуль для админов", callback_data='admin_module')
    button_feedback = types.InlineKeyboardButton("4 - Модуль для обратной связи", callback_data='feedback_module')
    button_tip = types.InlineKeyboardButton("5 - Совет дня", callback_data='tip_of_the_day')
    markup.add(button_simple)
    markup.add(button_complex)
    markup.add(button_admin)
    markup.add(button_feedback)
    markup.add(button_tip)
    return markup


def admin_module_menu():
    markup = types.InlineKeyboardMarkup()
    stat_btn = types.InlineKeyboardButton("Показать статистику", callback_data='show_statistic')
    reviews_btn = types.InlineKeyboardButton("Показать отзывы", callback_data='show_reviews')
    back_btn = types.InlineKeyboardButton("Назад", callback_data='back_to_main')
    markup.add(stat_btn)
    markup.add(reviews_btn)
    markup.add(back_btn)
    return markup


# Function to create the main menu for the complex module
def complex_module_menu():
    markup = types.InlineKeyboardMarkup()
    mode_button = types.InlineKeyboardButton("Выбрать режим", callback_data='select_mode')
    datetime_button = types.InlineKeyboardButton("Добавить дату и время", callback_data='include_datetime')
    cancel_mode_button = types.InlineKeyboardButton("Отменить режим", callback_data='cancel_mode')
    cancel_datetime_button = types.InlineKeyboardButton("Отключить дату и время", callback_data='cancel_datetime')
    ask_question_button = types.InlineKeyboardButton("Задать вопрос", callback_data='ask_complex_question')
    back_button = types.InlineKeyboardButton("Вернуться назад", callback_data='back_to_main')
    markup.add(mode_button, datetime_button)
    markup.add(cancel_mode_button, cancel_datetime_button)
    markup.add(ask_question_button)
    markup.add(back_button)
    return markup


# Function to handle mode selection
def mode_selection_menu():
    markup = types.InlineKeyboardMarkup()
    for mode_key in complex_modes:
        markup.add(types.InlineKeyboardButton(f"{mode_key.capitalize()}", callback_data=f'set_mode_{mode_key}'))
    back_button = types.InlineKeyboardButton("Вернуться в сложный модуль", callback_data='complex_module')
    markup.add(back_button)
    return markup


# Function to generate the AI's response
def handle_complex_question(chat_id, user_message, mode=None, include_datetime=False):
    try:
        # Prepare the prompt
        prompt = ""
        if mode:
            prompt += f"{complex_modes[mode]} "
        if include_datetime:
            now = datetime.datetime.now()
            day_of_week = now.strftime("%A")  # Get current day of the week
            current_time = now.strftime("%H:%M")  # Get current time in HH:MM format
            prompt += f"Current day of week: {day_of_week}, current time: {current_time}. "
        prompt += f"Question: {user_message}"

        # Generate a response using Hugging Face API
        ai_response = generate_response(prompt, hugging_face_token)
        response_message = f"Ваш вопрос: {user_message}\n\nОтвет AI:"
        if mode:
            response_message += f" ({mode.capitalize()})"
        response_message += f"\n{ai_response}"
        bot.send_message(chat_id, response_message)
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка при обработке AI: {e}")


# Function to fetch a random quote from an API
def get_random_quote():
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=5)
        if response.status_code == 200:
            data = response.json()
            quote = f"“{data[0]['q']}” – {data[0]['a']}"
            return quote
        else:
            raise Exception(f"API returned status code {response.status_code}")
    except Exception as e:
        print(f"Error fetching quote: {e}")
        # Fallback to a predefined quote
        return random.choice(FALLBACK_QUOTES)


def get_stat():
    with open('../admin/stat.json', 'r') as file:
        data = json.load(file)
        SIMPLE_MODULE_STATS = 'simple_module_stats'
        COMPLEX_MODULE_STATS = 'complex_module_stats'
        TIP_OF_THE_DAY_STATS = 'tip_of_the_day_stats'
        simple_usage = data[SIMPLE_MODULE_STATS]
        complex_usage = data[COMPLEX_MODULE_STATS]
        totd_usage = data[TIP_OF_THE_DAY_STATS]
        sum_usage = simple_usage + complex_usage + totd_usage
        str = f'суммарное количество использований: {sum_usage}\n' \
                f'Использование простого модуля: {simple_usage}({int(simple_usage/sum_usage*100)}%)\n'\
                f'Использование сложного модуля: {complex_usage}({int(complex_usage/sum_usage*100)}%)\n'\
                f'Использование модуля совета дня: {totd_usage}({int(totd_usage/sum_usage*100)}%)\n'
        return str


def increase_stat(module):
    with open('../admin/stat.json', 'r+') as file:
        data = json.load(file)
        data[module] += 1
        file.seek(0)
        json.dump(data, file)
        file.truncate()
        file.close()


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
        markup = main_menu()
        increase_stat(TIP_OF_THE_DAY_STATS)
        sent_message = bot.send_message(chat_id, "Добро пожаловать! Выберите опцию:", reply_markup=markup)
        # Сохраняем идентификатор отправленного сообщения с меню
        user_menu_messages[user_id] = sent_message.message_id
        user_states[user_id] = STATE_DEFAULT

    elif call.data == 'simple_module':
        # Устанавливаем состояние пользователя
        user_states[user_id] = STATE_AWAITING_SIMPLE_QUESTION
        markup = simple_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Привет, ты выбрал простой модуль, напиши вопрос:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id

    elif call.data == 'complex_module':
        # New complex module logic
        user_states[user_id] = STATE_SELECTING_COMPLEX_OPTION
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Вы выбрали сложный модуль. Выберите параметры или задайте вопрос:",
                              reply_markup=markup)

    elif call.data == 'select_mode':
        # Display the mode selection menu
        user_states[user_id] = STATE_SELECTING_COMPLEX_OPTION
        markup = mode_selection_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Выберите режим для ответа AI:", reply_markup=markup)

    elif call.data.startswith('set_mode_'):
        # Set the selected mode for the user
        mode = call.data.split('_')[-1]
        user_complex_preferences[user_id] = user_complex_preferences.get(user_id, {})
        user_complex_preferences[user_id]['mode'] = mode
        bot.answer_callback_query(call.id, f"Режим установлен: {mode.capitalize()}")
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text=f"Вы выбрали режим: {mode.capitalize()}. Теперь вы можете задать вопрос.",
                              reply_markup=markup)

    elif call.data == 'include_datetime':
        # Toggle datetime inclusion for the user
        user_complex_preferences[user_id] = user_complex_preferences.get(user_id, {})
        current_pref = user_complex_preferences[user_id].get('include_datetime', False)
        user_complex_preferences[user_id]['include_datetime'] = not current_pref
        status = "включено" if not current_pref else "отключено"
        bot.answer_callback_query(call.id, f"Добавление текущего дня и времени {status}.")
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text=f"Добавление текущего дня и времени {status}. Теперь вы можете задать вопрос.",
                              reply_markup=markup)

    elif call.data == 'cancel_mode':
        # Cancel the selected mode
        user_complex_preferences[user_id] = user_complex_preferences.get(user_id, {})
        if 'mode' in user_complex_preferences[user_id]:
            del user_complex_preferences[user_id]['mode']
            bot.answer_callback_query(call.id, "Режим сброшен.")
        else:
            bot.answer_callback_query(call.id, "Режим уже не установлен.")
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Режим сброшен. Выберите параметры или задайте вопрос.", reply_markup=markup)

    elif call.data == 'cancel_datetime':
        # Cancel datetime inclusion
        user_complex_preferences[user_id] = user_complex_preferences.get(user_id, {})
        if user_complex_preferences[user_id].get('include_datetime', False):
            user_complex_preferences[user_id]['include_datetime'] = False
            bot.answer_callback_query(call.id, "Добавление текущего дня и времени отключено.")
        else:
            bot.answer_callback_query(call.id, "Добавление текущего дня и времени уже отключено.")
        markup = complex_module_menu()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Добавление текущего дня и времени отключено. Выберите параметры или задайте вопрос.",
                              reply_markup=markup)

    elif call.data == 'ask_complex_question':
        # Prompt the user to send their question
        user_states[user_id] = STATE_AWAITING_COMPLEX_QUESTION
        back_button = types.InlineKeyboardMarkup()
        back_button.add(types.InlineKeyboardButton("Вернуться назад", callback_data='complex_module'))
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Введите ваш вопрос для сложного модуля:", reply_markup=back_button)

    elif call.data == 'back_to_main':
        # Сбрасываем состояние пользователя
        user_states[user_id] = STATE_DEFAULT
        markup = main_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Вы вернулись в главное меню. Выберите опцию:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id

    elif call.data == 'ask_another_question':
        # Пользователь хочет задать еще вопрос
        user_states[user_id] = STATE_AWAITING_SIMPLE_QUESTION
        markup = simple_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Напишите следующий вопрос:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id
    elif call.data == 'admin_module':
        if user_id in admin_ids:
            # Устанавливаем состояние пользователя
            user_states[user_id] = STATE_AWAITING_SIMPLE_QUESTION
            markup = admin_module_menu()

            # Редактируем предыдущее сообщение с новым текстом и клавиатурой
            bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text="Привет, мой дорогой и многоуважаемый админ, выбери опцию:", reply_markup=markup)
            # Обновляем идентификатор последнего сообщения с меню
            user_menu_messages[user_id] = message_id
        else:
            bot.answer_callback_query(call.id)
            delete_previous_menu(user_id, chat_id)
            bot.send_message(chat_id, 'еблан ты, а не админ')
            markup = main_menu()
            sent_message = bot.send_message(chat_id, "Добро пожаловать! Выберите опцию:", reply_markup=markup)
            # Сохраняем идентификатор отправленного сообщения с меню
            user_menu_messages[user_id] = sent_message.message_id
            user_states[user_id] = STATE_DEFAULT
    elif call.data == 'show_statistic':
        bot.answer_callback_query(call.id)
        delete_previous_menu(user_id, chat_id)
        bot.send_message(chat_id, get_stat())

        # Устанавливаем состояние пользователя
        user_states[user_id] = STATE_DEFAULT
        markup = admin_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.send_message(chat_id=chat_id,
                            text="Привет, мой дорогой и многоуважаемый админ, выбери опцию:", reply_markup=markup)
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
                            text="Привет, мой дорогой и многоуважаемый админ, выбери опцию:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id
    elif call.data == 'feedback_module':
        # Устанавливаем состояние пользователя
        user_states[user_id] = STATE_AWAITING_FEEDBACk
        markup = feedback_module_menu()

        # Редактируем предыдущее сообщение с новым текстом и клавиатурой
        bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                              text="Привет, мой недорогой и немногоуважаемый пользователь, напиши отзыв:", reply_markup=markup)
        # Обновляем идентификатор последнего сообщения с меню
        user_menu_messages[user_id] = message_id
    else:
        # Обработка других модулей (пока не реализованы)
        bot.answer_callback_query(call.id)
        delete_previous_menu(user_id, chat_id)
        bot.send_message(chat_id, "Данный модуль еще в разработке.")
        markup = main_menu()
        sent_message = bot.send_message(chat_id, "Добро пожаловать! Выберите опцию:", reply_markup=markup)
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

            sent_message = bot.send_message(chat_id, "Задавай ещё раз.", reply_markup=markup)
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
            handle_complex_question(chat_id, user_message, mode, include_datetime)
            user_states[user_id] = STATE_SELECTING_COMPLEX_OPTION
            bot.send_message(chat_id, "Вы можете задать следующий вопрос или вернуться в меню.",
                             reply_markup=complex_module_menu())
            increase_stat(COMPLEX_MODULE_STATS)
        elif state == STATE_AWAITING_FEEDBACk:
            delete_previous_menu(user_id, chat_id)
            user_message = message.text

            handle_user_feedback(user_id, user_message)

            user_states[user_id] = STATE_AWAITING_FEEDBACk
            sent_message = bot.send_message(chat_id, "Вы можете написать следующий отзыв или вернуться в меню.",
                             reply_markup=feedback_module_menu())
            user_menu_messages[user_id] = sent_message.message_id
        else:
            # Если состояние другое, игнорируем или отправляем сообщение
            bot.send_message(chat_id, "Пожалуйста, выберите опцию из меню.")
    else:
        # Если состояние не установлено, просим выбрать опцию из меню
        bot.send_message(chat_id, "Пожалуйста, выберите опцию из меню, используя команду /start.")


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

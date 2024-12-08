import telebot
from telebot import types
import configparser
import random
import datetime
from hugging_face_model import generate_response
from simple import QuestionAnalyzer


CONFIG = configparser.ConfigParser()
CONFIG.read('../configs/config.ini')

hugging_face_token = CONFIG['HUGGING_FACE_API']['hugging_face_token']

token = CONFIG['BOT.TELEGRAM']['token']
bot = telebot.TeleBot(token)

user_states = {}
user_menu_messages = {}

# Константы состояний
STATE_AWAITING_SIMPLE_QUESTION = "awaiting_simple_question"
STATE_SELECTING_COMPLEX_OPTION = "selecting_complex_option"
STATE_AWAITING_COMPLEX_QUESTION = "awaiting_complex_question"
STATE_IN_MAIN_MENU = "in_main_menu"
STATE_DEFAULT = "default"

complex_modes = {
    "philosopher": "Respond as a wise philosopher.",
    "politician": "Respond like a professional politician.",
    "teacher": "Respond like an experienced teacher."
}

user_complex_preferences = {}

anal = QuestionAnalyzer()


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
    markup.add(button_simple)
    markup.add(button_complex)
    markup.add(button_admin)
    markup.add(button_feedback)
    return markup


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


# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == 'simple_module':
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

            if not anal.is_yes_no_question(msg_text):
                bot.send_message(chat_id, "Некорректный вопрос")
            else:
                prob = random.randint(0, 1)
                if prob == 1:
                    sent_message = bot.send_message(chat_id, f'Вопрос: {msg_text}\nОтвет: Да')
                else:
                    sent_message = bot.send_message(chat_id, f'Вопрос: {msg_text}\nОтвет: No')

            sent_message = bot.send_message(chat_id, "Задавай ещё раз.", reply_markup=markup)
            # Сохраняем идентификатор отправленного сообщения с меню
            user_menu_messages[user_id] = sent_message.message_id
            # Остаемся в текущем состоянии или сбрасываем, если нужно
            # user_states[user_id] = STATE_DEFAULT
        elif state == STATE_AWAITING_COMPLEX_QUESTION:
            user_message = message.text
            preferences = user_complex_preferences.get(user_id, {})
            mode = preferences.get('mode')
            include_datetime = preferences.get('include_datetime', False)
            handle_complex_question(chat_id, user_message, mode, include_datetime)
            user_states[user_id] = STATE_SELECTING_COMPLEX_OPTION
            bot.send_message(chat_id, "Вы можете задать следующий вопрос или вернуться в меню.",
                             reply_markup=complex_module_menu())
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

import datetime

from hugging_face_model import generate_response
from telebot import types

complex_modes = {
    "philosopher": "Respond as a wise philosopher.",
    "politician": "Respond like a professional politician.",
    "teacher": "Respond like an experienced teacher."
}


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
def handle_complex_question(chat_id, hugging_face_token, user_message, mode=None, include_datetime=False):
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
        response_message = f"Ur question: {user_message}\n\nОтвет AI:"
        if mode:
            response_message += f" ({mode.capitalize()})"
        response_message += f"\n{ai_response}"

        return response_message
    except Exception as e:
        return f"Something went wrong: {e}"

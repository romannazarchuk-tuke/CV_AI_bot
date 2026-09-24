from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Надіслати вакансію")],
            [KeyboardButton(text="👀 Переглянути профіль"), KeyboardButton(text="✏️ Змінити інформацію")]
        ],
        resize_keyboard=True,
        is_persistent=True
    )
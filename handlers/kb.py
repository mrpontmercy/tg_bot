from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_keyboard(
    current_lesson_index, number_of_lessons, prefix
) -> InlineKeyboardMarkup:
    prev_ind = current_lesson_index - 1
    if prev_ind < 0:
        prev_ind = number_of_lessons - 1

    next_ind = current_lesson_index + 1
    if next_ind > number_of_lessons - 1:
        next_ind = 0

    keyboard = [
        [
            InlineKeyboardButton("<", callback_data=f"{prefix}{prev_ind}"),
            InlineKeyboardButton(
                f"{current_lesson_index + 1} / {number_of_lessons}", callback_data=" "
            ),
            InlineKeyboardButton(">", callback_data=f"{prefix}{next_ind}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

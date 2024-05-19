from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


KB_START_COMMAND = ReplyKeyboardMarkup(
    [["Активировать ключ"], ["Доступные занятия", "Мои занятия"], ["Отменить"]],
    one_time_keyboard=True,
    input_field_placeholder="Что вы хотите сделать?",
)


def get_flip_with_cancel_INLINEKB(
    current_lesson_index, number_of_lessons, prefix
) -> InlineKeyboardMarkup:
    keyboard = _get_flip_keyboard(current_lesson_index, number_of_lessons, prefix)
    keyboard.append([InlineKeyboardButton("Отменить", callback_data=f"{prefix}cancel")])
    return InlineKeyboardMarkup(keyboard)


def get_lesson_INLINEKB(
    current_lesson_index, number_of_lessons, prefix
) -> InlineKeyboardMarkup:
    prev_ind = current_lesson_index - 1
    if prev_ind < 0:
        prev_ind = number_of_lessons - 1

    next_ind = current_lesson_index + 1
    if next_ind > number_of_lessons - 1:
        next_ind = 0

    keyboard = _get_flip_keyboard(current_lesson_index, number_of_lessons, prefix)
    keyboard.append(
        [InlineKeyboardButton("Записаться", callback_data=f"{prefix}subscribe")]
    )
    return InlineKeyboardMarkup(keyboard)


def _get_flip_keyboard(current_lesson_index, number_of_lessons, prefix):
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
        ],
    ]
    return keyboard

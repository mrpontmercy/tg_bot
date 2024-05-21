from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


KB_START_COMMAND = ReplyKeyboardMarkup(
    [
        ["Регистрация", "Активировать ключ"],
        ["Доступные занятия", "Мои занятия"],
        ["Отменить"],
    ],
    one_time_keyboard=True,
    input_field_placeholder="Что вы хотите сделать?",
)

KB_START_COMMAND_REGISTERED = ReplyKeyboardMarkup(
    [
        ["Активировать ключ", "Оставшееся количество занятий"],
        ["Доступные занятия", "Мои занятия"],
        ["Отменить"],
    ],
    one_time_keyboard=True,
    input_field_placeholder="Что вы хотите сделать?",
)

KB_START_COMMAND_REGISTERED = ReplyKeyboardMarkup(
    [
        ["Мои занятия"],
        ["Отменить"],
    ],
    one_time_keyboard=True,
    input_field_placeholder="Что вы хотите сделать?",
)

KB_ADMIN_COMMAND = ReplyKeyboardMarkup(
    [
        ["Создать ключ", "Доступные ключи"],
        ["Обновить уроки", "Добавить преподователя"],
    ],
    one_time_keyboard=True,
)


def get_confirmation_keyboard(prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Подтвердить", callback_data=f"{prefix}_confirm_action"
                ),
                InlineKeyboardButton(
                    "Отменить", callback_data=f"{prefix}_cancel_action"
                ),
            ]
        ]
    )
    return kb


def get_flip_with_cancel_INLINEKB(
    current_lesson_index, number_of_lessons, prefix
) -> InlineKeyboardMarkup:
    keyboard = _get_flip_keyboard(current_lesson_index, number_of_lessons, prefix)
    keyboard.append([InlineKeyboardButton("Отменить", callback_data=f"{prefix}cancel")])
    return InlineKeyboardMarkup(keyboard)


def get_flip_keyboard(current_lesson_index, number_of_lessons, prefix):
    keyboard = _get_flip_keyboard(current_lesson_index, number_of_lessons, prefix)
    keyboard.append(
        [InlineKeyboardButton("Удалить", callback_data=f"{prefix}deleteSub")]
    )
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

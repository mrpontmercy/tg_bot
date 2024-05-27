from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from config import (
    CALLBACK_DATA_CANCEL_LESSON,
    CALLBACK_DATA_DELETE_LESSON,
    CALLBACK_DATA_DELETESUBSCRIPTION,
    CALLBACK_DATA_EDIT_LESSON,
    CALLBACK_DATA_EDIT_TIMESTART_LESSON,
    CALLBACK_DATA_EDIT_TITLE_LESSON,
    CALLBACK_DATA_SUBSCRIBE,
)

KB_START_COMMAND = ReplyKeyboardMarkup(
    [
        ["Регистрация", "Активировать ключ"],
        ["Доступные занятия", "Мои занятия"],
        ["Отменить"],
    ],
    one_time_keyboard=False,
    input_field_placeholder="Что вы хотите сделать?",
)

KB_START_COMMAND_ADMIN = ReplyKeyboardMarkup(
    [
        ["Регистрация", "Активировать ключ"],
        ["Доступные занятия", "Мои занятия", "Админ панель"],
        ["Отменить"],
    ],
    one_time_keyboard=False,
    input_field_placeholder="Что вы хотите сделать?",
)

KB_START_COMMAND_REGISTERED = ReplyKeyboardMarkup(
    [
        ["Активировать ключ", "Оставшееся количество занятий"],
        ["Доступные занятия", "Мои занятия"],
        ["Отменить"],
    ],
    one_time_keyboard=False,
    input_field_placeholder="Что вы хотите сделать?",
)

KB_START_COMMAND_REGISTERED_ADMIN = ReplyKeyboardMarkup(
    [
        ["Активировать ключ", "Оставшееся количество занятий"],
        ["Доступные занятия", "Мои занятия", "Админ панель"],
        ["Отменить"],
    ],
    one_time_keyboard=False,
    input_field_placeholder="Что вы хотите сделать?",
)

KB_START_COMMAND_REGISTERED_LECTURER = ReplyKeyboardMarkup(
    [
        ["Ваши занятия", "Добавить занятие"],
        ["Отменить"],
    ],
    one_time_keyboard=False,
    input_field_placeholder="Что вы хотите сделать?",
)

KB_START_COMMAND_REGISTERED_LECTURER_ADMIN = ReplyKeyboardMarkup(
    [
        ["Ваши занятия", "Админ панель"],
        ["Отменить"],
    ],
    one_time_keyboard=False,
    input_field_placeholder="Что вы хотите сделать?",
)

KB_ADMIN_COMMAND = ReplyKeyboardMarkup(
    [
        ["Создать ключ", "Доступные ключи"],
        ["Обновить уроки", "Добавить преподователя"],
        ["Назад"],
    ],
    one_time_keyboard=False,
)

KB_LECTURER_EDIT_LESSON = ReplyKeyboardMarkup(
    [
        [
            "Изменить заголовок",
            "Изменить дату и время",
        ],
        [
            "Назад",
        ],
    ]
)


def get_edit_lesson_kb(prefix):
    keyboard = [
        [
            InlineKeyboardButton(
                "Изменить заголовок",
                callback_data=f"{prefix}{CALLBACK_DATA_EDIT_TITLE_LESSON}",
            ),
            InlineKeyboardButton(
                "Изменить дату и время",
                callback_data=f"{prefix}{CALLBACK_DATA_EDIT_TIMESTART_LESSON}",
            ),
        ],
        [InlineKeyboardButton("Назад", callback_data=f"{prefix}_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


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


def get_flipKB_with_edit(current_lesson_index, number_of_lessons, prefix):
    keyboard = _get_flip_keyboard(current_lesson_index, number_of_lessons, prefix)
    keyboard.append(
        [
            InlineKeyboardButton(
                "Изменить", callback_data=f"{prefix}{CALLBACK_DATA_EDIT_LESSON}"
            ),
            InlineKeyboardButton(
                "Удалить", callback_data=f"{prefix}{CALLBACK_DATA_DELETE_LESSON}"
            ),
        ]
    )
    return InlineKeyboardMarkup(keyboard)


def get_flip_with_cancel_INLINEKB(
    current_lesson_index, number_of_lessons, prefix
) -> InlineKeyboardMarkup:
    keyboard = _get_flip_keyboard(current_lesson_index, number_of_lessons, prefix)
    keyboard.append(
        [
            InlineKeyboardButton(
                "Отменить", callback_data=f"{prefix}{CALLBACK_DATA_CANCEL_LESSON}"
            )
        ]
    )
    return InlineKeyboardMarkup(keyboard)


def get_flip_keyboard(current_lesson_index, number_of_lessons, prefix):
    keyboard = _get_flip_keyboard(current_lesson_index, number_of_lessons, prefix)
    keyboard.append(
        [
            InlineKeyboardButton(
                "Удалить", callback_data=f"{prefix}{CALLBACK_DATA_DELETESUBSCRIPTION}"
            )
        ]
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
        [
            InlineKeyboardButton(
                "Записаться", callback_data=f"{prefix}{CALLBACK_DATA_SUBSCRIBE}"
            )
        ]
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

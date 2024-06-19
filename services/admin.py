import os
import random
import re
import string

from telegram import Document
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import LECTURER_STATUS
from db import fetch_all
from services.db import (
    execute_delete,
    execute_update,
    get_user_by_phone_number,
    insert_lesson_in_db,
)
from services.exceptions import InputMessageError, SubscriptionError, UserError
from services.kb import KB_ADMIN_COMMAND
from services.lesson import get_lessons_from_file
from services.reply_text import send_error_message
from services.utils import (
    PHONE_NUMBER_PATTERN,
    Subscription,
    TransientLesson,
    get_saved_lessonfile_path,
    make_lesson_params,
)


unity = string.ascii_letters + string.digits


async def generate_sub_key(k: int):
    try:
        subs = await get_all_subs()
    except SubscriptionError as e:
        subs = []
        pass

    while True:
        sub_key = "".join(random.choices(unity, k=k))
        if not any([True if sub_key == el.sub_key else False for el in subs]):
            break

    return sub_key


async def get_lecturer_and_error_by_phone(phone_number):
    try:
        lecturer = await get_user_by_phone_number(phone_number)
    except UserError:
        return None, f"Нет пользователя с номером {phone_number}"
    else:
        if lecturer.status != LECTURER_STATUS:
            return (
                None,
                f"Пользователь с номером {phone_number} не является преподавателем",
            )

    return lecturer, None


async def process_insert_lesson_into_db(
    recieved_file: Document,
    user_tg_id: int,
    context: ContextTypes.DEFAULT_TYPE,
):
    file_path = await get_saved_lessonfile_path(recieved_file, context)

    lessons = get_lessons_from_file(file_path)
    os.remove(file_path)
    if lessons is None or not lessons:
        return (
            False,
            "Неверно заполнен файл. Возможно файл пустой. Попробуй с другим файлом.",
        )
    errors_after_inserting_lessons = await insert_lessons_into_db(lessons)

    if errors_after_inserting_lessons:
        await context.bot.send_message(
            user_tg_id,
            "\n".join([row[0] for row in errors_after_inserting_lessons]),
        )

    err_lesson = ";\n".join([row[-1] for row in errors_after_inserting_lessons])
    if len(lessons) == len(errors_after_inserting_lessons):
        answer = "Ни одного урока не было добавлено!"
    else:
        answer = f"Все уроки, кроме\n<b>{err_lesson}</b>\nбыли добавлены в общий список"
    return True, answer
    await context.bot.send_message(
        chat_id=user_tg_id,
        text=answer,
        reply_markup=KB_ADMIN_COMMAND,
        parse_mode=ParseMode.HTML,
    )
    return True


async def insert_lessons_into_db(lessons: list[TransientLesson]):
    res_err = []

    for lesson in lessons:
        lecturer, message = await get_lecturer_and_error_by_phone(lesson.lecturer_phone)
        if lecturer is None:
            res_err.append((message, lesson.title))
            continue

        params = make_lesson_params(lesson, lecuturer_id=lecturer.id)
        # TODO Возможно стоит переписать под executemany чтобы был только один запрос
        await insert_lesson_in_db(params)
    return res_err


async def delete_subscription(sub_id: int):
    await execute_delete("subscription", "id=:sub_id", {"sub_id": sub_id})


async def update_user_to_lecturer(user_id):
    await execute_update(
        "user",
        "status=:status",
        "id=:user_id",
        {
            "status": LECTURER_STATUS,
            "user_id": user_id,
        },
    )


def validate_phone_number(message: str):
    message = message.split(" ")
    if len(message) != 1:
        raise InputMessageError("Количество слов в сообщение должно быть равным 1")

    if not re.fullmatch(PHONE_NUMBER_PATTERN, message[0]):
        raise InputMessageError(
            "Сообщение должно содержать номер телефона. Начинается с 8. Всего 11 цифр"
        )

    return message[0]


def validate_num_of_classes(message: str):
    message = message.split(" ")
    if len(message) != 1:
        raise InputMessageError("Количество слов в сообщение должно быть равным 1")

    if not re.fullmatch("\d+", message[0]):
        raise InputMessageError("Сообщение должно содержать только цифры")

    return message[0]


async def get_all_subs():
    r_sql = """SELECT * FROM subscription"""

    subs = await fetch_all(r_sql)
    if not subs:
        raise SubscriptionError("Не удалось найти ни одного абонимента!")

    result = []
    for sub in subs:
        result.append(Subscription(**sub))

    return result


async def get_available_subs() -> list[Subscription]:
    r_sql = """SELECT * FROM subscription WHERE user_id IS NULL"""

    subs = await fetch_all(r_sql)
    if not subs:
        raise SubscriptionError("Не удалось найти доступные абонементы!")
    result = []
    for sub in subs:
        result.append(Subscription(**sub))

    return result

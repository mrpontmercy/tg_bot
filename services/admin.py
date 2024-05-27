import random
import re
import string

from telegram import Document
from telegram.ext import ContextTypes
from config import LECTURER_STR, LESSONS_DIR
from db import execute, fetch_all
from services.db import execute_delete, execute_update, get_user_by_phone_number
from services.exceptions import InputMessageError, SubscriptionError, UserError
from services.utils import PHONE_NUMBER_PATTERN, Subscription, TransientLesson


unity = string.ascii_letters + string.digits


async def generate_sub_key(k: int):
    try:
        subs = await get_all_subs()
    except SubscriptionError as e:
        pass
    else:
        subs = []
    while True:
        sub_key = "".join(random.choices(unity, k=k))
        if not any([True if sub_key in el else False for el in subs]):
            break

    return sub_key


async def save_file(recived_file: Document, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(recived_file)
    saved_file_path = LESSONS_DIR / recived_file.file_name
    await file.download_to_drive(saved_file_path)
    return saved_file_path


async def get_lecturer_by_phone(phone_number):
    try:
        lecturer = await get_user_by_phone_number(phone_number)
    except UserError:
        return None, f"Нет пользователя с номером {phone_number}"
    else:
        if lecturer.status != LECTURER_STR:
            return (
                None,
                f"Пользователь с номером {phone_number} не является преподавателем",
            )

    return lecturer, None


async def insert_lessons_into_db(lessons: list[TransientLesson]):
    res_err = []
    for lesson in lessons:
        lecturer, message = await get_lecturer_by_phone(lesson.lecturer_phone)
        if lecturer is None:
            res_err.append((message, lesson.title))
            continue

        params = lesson.to_dict()
        del params["lecturer_phone"]
        params["lecturer_id"] = lecturer.id
        # TODO Возможно стоит переписать под executemany чтобы был только один запрос
        await execute(
            """INSERT INTO lesson (title, time_start, num_of_seats, lecturer_id) VALUES (:title, :time_start,:num_of_seats, :lecturer_id)""",
            params,
        )
    return res_err


async def delete_subscription(sub_id: int):
    await execute_delete("subscription", "id=:sub_id", {"sub_id": sub_id})


async def update_user_to_lecturer(user_id):
    await execute_update(
        "user",
        "status=:status",
        "id=:user_id",
        {
            "status": LECTURER_STR,
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
        raise SubscriptionError("Не удалось найти абонементы!")

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

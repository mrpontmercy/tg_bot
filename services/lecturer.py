import logging
import re

from aiosqlite import Error
from telegram.ext import ContextTypes

from db import get_db
from services.notification import _notify_lesson_users
from services.admin import validate_num_of_classes
from services.db import execute_delete, execute_update, get_all_users_of_lesson
from services.exceptions import InputMessageError
from services.reply_text import send_error_message
from services.states import EditLessonState
from services.utils import Lesson, DATE_TIME_PATTERN


async def process_cancel_lesson_by_lecturer(
    lesson: Lesson, context: ContextTypes.DEFAULT_TYPE
):
    # Обязательно включать PRAGMA foreign_keys = on
    params_lesson_id = {"lesson_id": lesson.id}

    all_students_of_lesson = await get_all_users_of_lesson(params_lesson_id)
    print(f"{params_lesson_id=}")
    print(f"{all_students_of_lesson=}")
    ok = await process_delete_lesson_db(params_lesson_id)

    if not ok:
        return "Ошибка. Операцию выполнить не удалось!"
    if all_students_of_lesson is None:
        return "Нет записанных студентов.\n\nУрок успешно отменен."

    data = {
        "title": lesson.title,
        "time_start": lesson.time_start,
        "lecturer": lesson.lecturer_full_name,
    }

    await _notify_lesson_users(
        "cancel_lesson_message.jinja", data, all_students_of_lesson, context
    )

    await (await get_db()).commit()
    return "Урок успешно отменен"


async def process_delete_lesson_db(params_lesson_id):
    try:
        await execute_update(
            "subscription",
            "num_of_classes=num_of_classes + 1",
            "user_id IN (SELECT user_id from user_lesson where lesson_id=:lesson_id)",
            params=params_lesson_id,
            autocommit=False,
        )

        await execute_delete(
            "lesson", "id=:lesson_id", params=params_lesson_id, autocommit=False
        )
    except Error as e:
        logging.getLogger(__name__).exception(e)
        await (await get_db()).rollback()
        return False
    await (await get_db()).commit()
    return True


async def change_lesson_title(
    user_tg_id, message: str, context: ContextTypes.DEFAULT_TYPE
):
    curr_lesson: Lesson | None = context.user_data.get("curr_lesson", None)

    if curr_lesson is None:
        await send_error_message(user_tg_id, context, err="Не удалось найти урок")
        return EditLessonState.CHOOSE_OPTION

    new_title = " ".join(message.split(" "))

    data = {
        "old_title": curr_lesson.title,
        "new_title": new_title,
        "time_start": curr_lesson.time_start,
    }

    await execute_update(
        "lesson",
        "title=:title",
        "lecturer_id=:lecturer_id AND id=:lesson_id",
        params={
            "title": new_title,
            "lecturer_id": curr_lesson.lecturer_id,
            "lesson_id": curr_lesson.id,
        },
    )

    all_users_of_lesson = await get_all_users_of_lesson({"lesson_id": curr_lesson.id})
    if all_users_of_lesson is not None:
        await _notify_lesson_users(
            "edit_title_lesson.jinja", data, all_users_of_lesson, context
        )
    return None


async def change_lesson_time_start(
    user_tg_id, message: str, context: ContextTypes.DEFAULT_TYPE
):
    curr_lesson: Lesson | None = context.user_data.get("curr_lesson", None)

    if curr_lesson is None:
        await send_error_message(user_tg_id, context, err="Не удалось найти урок")
        return EditLessonState.CHOOSE_OPTION

    validated_time_start = _validate_datetime(message)

    if not validated_time_start:
        await send_error_message(
            user_tg_id,
            context,
            err="Неверный формат даты и времени!\nПопробуйте снова.",
        )
        return EditLessonState.EDIT_TIMESTART

    data = {
        "title": curr_lesson.title,
        "old_time_start": curr_lesson.time_start,
        "new_time_start": validated_time_start,
    }

    await execute_update(
        "lesson",
        "time_start=:time_start",
        "lecturer_id=:lecturer_id AND id=:lesson_id",
        params={
            "time_start": message,
            "lecturer_id": curr_lesson.lecturer_id,
            "lesson_id": curr_lesson.id,
        },
    )

    all_users_of_lesson = await get_all_users_of_lesson({"lesson_id": curr_lesson.id})
    if all_users_of_lesson is not None:
        await _notify_lesson_users(
            "edit_time_start_lesson.jinja", data, all_users_of_lesson, context
        )
    return None


async def change_lesson_num_of_seats(
    user_tg_id, message: str, context: ContextTypes.DEFAULT_TYPE
):
    curr_lesson: Lesson | None = context.user_data.get("curr_lesson", None)

    if curr_lesson is None:
        await send_error_message(user_tg_id, context, err="Не удалось найти урок")
        return EditLessonState.CHOOSE_OPTION

    try:
        num_of_seats = validate_num_of_classes(message)
    except InputMessageError as e:
        await send_error_message(user_tg_id, context, err=str(e))
        return None

    await execute_update(
        "lesson",
        "num_of_seats=:num_of_seats",
        "lecturer_id=:lecturer_id AND id=:lesson_id",
        params={
            "num_of_seats": num_of_seats,
            "lecturer_id": curr_lesson.lecturer_id,
            "lesson_id": curr_lesson.id,
        },
    )

    return None


def _validate_datetime(message: str):
    if re.fullmatch(DATE_TIME_PATTERN, message):
        return True
    return False

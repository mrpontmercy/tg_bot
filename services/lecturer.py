import re
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from db import execute, fetch_all, get_db
from handlers.begin import get_current_keyboard
from services.db import execute_delete, execute_update, get_users_by_id
from services.reply_text import send_error_message
from services.states import EditLessonState
from services.templates import render_template
from services.utils import Lesson


datetime_pattern = r"^\d{4}-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01]) (0?[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"


async def process_cancel_lesson_by_lecturer(
    lesson: Lesson, context: ContextTypes.DEFAULT_TYPE
):
    # Обязательно включать PRAGMA foreign_keys = on
    params_lesson_id = {"lesson_id": lesson.id}

    await process_delete_lesson_db(params_lesson_id)

    all_students_of_lesson = await get_all_users_of_lesson(params_lesson_id)

    if all_students_of_lesson is None:
        return "Урок успешно отменен.\nНет записанных студентов. Сообщения об отмене никому не отправлялось"

    data = {
        "title": lesson.title,
        "time_start": lesson.time_start,
        "lecturer": lesson.lecturer,
    }

    await _notify_lesson_users(
        "cancel_lesson_message.jinja", data, all_students_of_lesson, context
    )

    await (await get_db()).commit()
    return "Урок успешно отменен"


async def get_all_users_of_lesson(params_lesson_id: dict):
    user_ids = await fetch_all(
        "SELECT user_id from user_lesson where lesson_id=:lesson_id", params_lesson_id
    )

    all_students_of_lesson = await get_users_by_id(
        [v for item in user_ids for v in item.values()]
    )

    return all_students_of_lesson


async def process_delete_lesson_db(params_lesson_id):
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


async def _notify_lesson_users(
    template_name: str, data: dict, all_students_of_lesson, context
):
    message_to_users = render_template(template_name, data=data, replace=False)

    for student in all_students_of_lesson:
        await context.bot.send_message(
            student.telegram_id,
            render_template("notification.jinja", data={"message": message_to_users}),
            parse_mode=ParseMode.HTML,
        )


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
            user_tg_id, context, err="Неверный формат даты и времени!"
        )
        return EditLessonState.CHOOSE_OPTION

    data = {
        "title": curr_lesson.title,
        "old_time_start": curr_lesson.time_start,
        "new_time_start": message,
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
    await _notify_lesson_users(
        "edit_time_start_lesson.jinja", data, all_users_of_lesson, context
    )
    return None


def _validate_datetime(message: str):
    if re.fullmatch(datetime_pattern, message):
        return True
    return False

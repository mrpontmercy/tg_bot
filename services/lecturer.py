from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from db import execute, fetch_all, get_db
from services.db import execute_delete, execute_update, get_users_by_id
from services.templates import render_template
from services.utils import Lesson


async def process_cancel_lesson_by_lecturer(
    lesson: Lesson, context: ContextTypes.DEFAULT_TYPE
):
    # Обязательно включать PRAGMA foreign_keys = on
    params_lesson_id = {"lesson_id": lesson.id}
    user_ids = await fetch_all(
        "SELECT user_id from user_lesson where lesson_id=:lesson_id", params_lesson_id
    )
    print(f"{user_ids=}")
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
    all_students_of_lesson = await get_users_by_id(
        [v for item in user_ids for v in item.values()]
    )
    if all_students_of_lesson is None:
        return "Урок успешно отменен.\nНет записанных студентов. Сообщения об отмене никому не отправлялось"

    data = {
        "title": lesson.title,
        "time_start": lesson.time_start,
        "lecturer": lesson.lecturer,
    }
    message_to_users = render_template("cancel_lesson_message.jinja", data=data)
    for student in all_students_of_lesson:
        await context.bot.send_message(
            student.telegram_id,
            render_template("notification.jinja", data={"message": message_to_users}),
            parse_mode=ParseMode.HTML,
        )

    await (await get_db()).commit()
    return "Урок успешно отменен"

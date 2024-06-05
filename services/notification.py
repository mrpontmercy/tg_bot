import logging

from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from services.db import get_user_by_tg_id, get_user_by_id
from services.exceptions import UserError
from services.templates import render_template
from services.utils import Lesson


async def notify_lecturer_user_cancel_lesson(
    user_full_name: str,
    lecturer_id: int,
    lesson: Lesson,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        lecturer = await get_user_by_id(lecturer_id)  # ???
    except UserError as e:
        logging.getLogger(__name__).exception(e)
        return None
    message = render_template(
        "notify_lecturer_user_cancel_lesson.jinja",
        data={
            "user_full_name": user_full_name,
            "title": lesson.title,
            "time_start": lesson.time_start,
        },
        replace=False,
    )

    await context.bot.send_message(
        lecturer.telegram_id,
        render_template("notification.jinja", data={"message": message}),
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

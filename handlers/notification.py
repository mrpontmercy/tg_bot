import logging

from telegram.ext import ContextTypes
from services.db import get_user_by_tg_id, get_user_by_id
from services.exceptions import UserError
from services.templates import render_template
from services.utils import Lesson


async def notify_lecturer(
    lecturer_id: int, lesson: Lesson, context: ContextTypes.DEFAULT_TYPE
):
    try:
        lecturer = await get_user_by_id(lecturer_id)  # ???
    except UserError as e:
        logging.getLogger(__name__).exception(e)
        return None

    await context.bot.send_message(
        lecturer.telegram_id,
        render_template(
            "notify_lecturer.jinja",
            {"title": lesson.title, "time_start": lesson.time_start},
        ),
    )

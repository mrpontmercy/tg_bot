from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from db import execute, fetch_all
from services.db import get_user, get_users_by_id
from services.exceptions import UserError
from services.lecturer import process_cancel_lesson_by_lecturer
from services.reply_text import send_error_message
from services.states import StartHandlerStates
from services.templates import render_template
from services.utils import Lesson


async def cancel_lesson_by_lecturer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обновить количество занятий на абонементе
    Удалить все связанные уроки из user_lesson
    Удалить урок из lesson
    Отправить всем студентам, кто записан на урок уведомление об отмене урока
    """
    query = update.callback_query
    await query.answer()

    lesson = context.user_data.get("curr_lesson", None)
    if lesson is None:
        await context.bot.send_message(
            update.effective_user.id, "Не удалось найти урок!"
        )
        return StartHandlerStates.START
    try:
        lecturer = await get_user(update.effective_user.id)
    except UserError as e:
        await send_error_message(update.effective_user.id, context, err=str(e))
        return StartHandlerStates.START

    if lecturer.status != "Преподаватель":
        await send_error_message(
            update.effective_user.id,
            context,
            err="Пользователь не является преподавателем",
        )
        return StartHandlerStates.START

    result_message = await process_cancel_lesson_by_lecturer(lesson, context)

    await context.bot.send_message(
        lecturer.telegram_id, result_message, parse_mode=ParseMode.HTML
    )
    return StartHandlerStates.START

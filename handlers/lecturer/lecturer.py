from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from handlers.begin import get_current_keyboard
from services.db import execute_update, get_user
from services.exceptions import UserError
from services.kb import KB_LECTURER_EDIT_LESSON
from services.lecturer import (
    change_lesson_time_start,
    change_lesson_title,
    process_cancel_lesson_by_lecturer,
)
from services.register import lecturer_required, user_required
from services.reply_text import send_error_message
from services.states import EditLessonState, StartHandlerState
from services.templates import render_template
from services.utils import Lesson

from config import (
    LECTURER_STR,
)


@user_required(EditLessonState.CHOOSE_OPTION)
@lecturer_required(EditLessonState.CHOOSE_OPTION)
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
        return EditLessonState.CHOOSE_OPTION
    try:
        lecturer = await get_user(update.effective_user.id)
    except UserError as e:
        await send_error_message(update.effective_user.id, context, err=str(e))
        return EditLessonState.CHOOSE_OPTION

    if lecturer.status != LECTURER_STR:
        await send_error_message(
            update.effective_user.id,
            context,
            err="Пользователь не является преподавателем",
        )
        return EditLessonState.CHOOSE_OPTION

    result_message = await process_cancel_lesson_by_lecturer(lesson, context)

    await context.bot.send_message(
        lecturer.telegram_id, result_message, parse_mode=ParseMode.HTML
    )
    return EditLessonState.CHOOSE_OPTION


@user_required(StartHandlerState.START)
@lecturer_required(StartHandlerState.START)
async def begin_edit_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_tg_id = update.effective_user.id

    curr_lesson: Lesson | None = context.user_data.get("curr_lesson")

    if curr_lesson is None:
        await context.bot.send_message(user_tg_id, "Что-то пошло не так!")
        return EditLessonState.CHOOSE_OPTION

    user = await get_user(user_tg_id)

    if user.status != LECTURER_STR:
        await send_error_message(
            user_tg_id, context, err="Пользователь не является преподавателем"
        )
        return EditLessonState.CHOOSE_OPTION

    if curr_lesson.lecturer_id != user.id:
        await context.bot.send_message(user_tg_id, "Что-то пошло не так!")
        return EditLessonState.CHOOSE_OPTION

    await context.bot.send_message(
        user_tg_id,
        render_template(
            "edit_lesson.jinja",
            data={"title": curr_lesson.title, "time_start": curr_lesson.time_start},
        ),
        reply_markup=KB_LECTURER_EDIT_LESSON,
        parse_mode=ParseMode.HTML,
    )
    return EditLessonState.CHOOSE_OPTION


@user_required(ConversationHandler.END)
@lecturer_required(ConversationHandler.END)
async def enter_title_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        update.effective_user.id, "Отправьте новый заголовок занятия!"
    )
    return EditLessonState.EDIT_TITLE


@user_required(ConversationHandler.END)
@lecturer_required(ConversationHandler.END)
async def enter_time_start_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        update.effective_user.id, "Отправьте новую дату и время занятия"
    )
    return EditLessonState.EDIT_TIMESTART


@user_required(ConversationHandler.END)
@lecturer_required(ConversationHandler.END)
async def edit_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg_id = update.effective_user.id

    state = await change_lesson_title(user_tg_id, update.message.text, context)

    if state:
        return state

    kb = await get_current_keyboard(update)
    await context.bot.send_message(
        user_tg_id, "Заголовок урока успешно обновлен", reply_markup=kb
    )
    return EditLessonState.CHOOSE_OPTION


@user_required(ConversationHandler.END)
@lecturer_required(ConversationHandler.END)
async def edit_time_start_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg_id = update.effective_user.id

    state = await change_lesson_time_start(user_tg_id, update.message.text, context)

    if state:
        return state

    kb = await get_current_keyboard(update)
    await context.bot.send_message(
        user_tg_id, "Дата занятия успешно обновлена", reply_markup=kb
    )
    return EditLessonState.CHOOSE_OPTION

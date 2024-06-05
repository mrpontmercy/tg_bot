import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from handlers.begin import get_current_keyboard
from handlers.start.lesson import _lessons_button
from services.utils import (
    get_saved_lessonfile_path,
    make_lessons_params,
)
from services.db import (
    get_lecturer_upcomming_lessons,
    get_user_by_tg_id,
    insert_lessons_into_db,
)
from services.kb import KB_LECTURER_EDIT_LESSON, get_flipKB_with_edit
from services.lecturer import (
    change_lesson_time_start,
    change_lesson_title,
    process_cancel_lesson_by_lecturer,
)
from services.lesson import get_lessons_button, get_lessons_from_file
from services.register import lecturer_required, user_required
from services.reply_text import send_error_message
from services.states import EditLessonState, StartHandlerState
from services.templates import render_template
from services.utils import Lesson, make_lesson_params

from config import (
    CALLBACK_LECTURER_LESSON_PREFIX,
    LECTURER_STATUS,
)


@user_required(StartHandlerState.START)
@lecturer_required(StartHandlerState.START)
async def send_file_lessons_lecturer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user_tg_id = update.effective_user.id
    await context.bot.send_message(
        user_tg_id,
        "Отправьте файл *.csv установленного образца. Либо нажмите Отмена чтобы завершить операцию!",
    )
    return StartHandlerState.SEND_FILE_LESSONS_LECTURER


@user_required(StartHandlerState.START)
@lecturer_required(StartHandlerState.START)
async def insert_lessons_from_file_lecturer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Считать лист TrLesson из файл
    сформировать лист диктов для вставки занятий в бд
    Вставить полученный лист диктолв в бд

    """
    rec_document = update.message.document
    user_tg_id = update.effective_user.id

    lecturer = await get_user_by_tg_id(user_tg_id)

    file_path = await get_saved_lessonfile_path(rec_document, context)
    lessons = get_lessons_from_file(
        file_path, fieldnames=("title", "time_start", "num_of_seats")
    )
    os.remove(file_path)
    if lessons is None or not lessons:
        await send_error_message(
            user_tg_id,
            context,
            err="Неверно заполнен файл. Возможно файл пустой. Попробуй с другим файлом.",
        )
        # TODO добавить верный стейт
        return 0
    params = make_lessons_params(lessons, lecuturer_id=lecturer.id)

    await insert_lessons_into_db(params)
    await context.bot.send_message(user_tg_id, "Уроки успешно добавлены")
    return StartHandlerState.START


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
    lesson = context.user_data.get("curr_lesson", None)
    if lesson is None:
        await context.bot.send_message(
            update.effective_user.id, "Не удалось найти урок!"
        )
        return EditLessonState.CHOOSE_OPTION

    result_message = await process_cancel_lesson_by_lecturer(lesson, context)

    await query.edit_message_text(result_message, parse_mode=ParseMode.HTML)
    return EditLessonState.CHOOSE_OPTION


@user_required(StartHandlerState.START)
@lecturer_required(EditLessonState.CHOOSE_OPTION)
async def begin_edit_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_tg_id = update.effective_user.id

    curr_lesson: Lesson | None = context.user_data.get("curr_lesson")

    if curr_lesson is None:
        await context.bot.send_message(user_tg_id, "Что-то пошло не так!")
        return EditLessonState.CHOOSE_OPTION

    user = await get_user_by_tg_id(user_tg_id)

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


@user_required(StartHandlerState.START)
@lecturer_required(StartHandlerState.START)
async def show_lecturer_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg_id = update.effective_user.id

    lecturer = await get_user_by_tg_id(telegram_id=user_tg_id)

    context.user_data["curr_user_tg_id"] = lecturer.telegram_id
    lessons = await get_lecturer_upcomming_lessons(lecturer.id)

    if lessons is None:
        await send_error_message(user_tg_id, context, err="У вас ещё нет занятий.")
        return StartHandlerState.START
    context.user_data["curr_lesson"] = lessons[0]
    kb = get_flipKB_with_edit(
        0,
        len(lessons),
        CALLBACK_LECTURER_LESSON_PREFIX,
    )
    await context.bot.send_message(
        user_tg_id,
        text=render_template("lesson.jinja", data=lessons[0].to_dict_lesson_info()),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )
    return StartHandlerState.START


@user_required(StartHandlerState.START)
@lecturer_required(StartHandlerState.START)
async def lecturer_lessons_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lessons, state = await get_lessons_button(
        update,
        context,
        get_lecturer_upcomming_lessons,
        StartHandlerState.START,
    )

    if lessons is None:
        return state

    kb_func = get_flipKB_with_edit
    await _lessons_button(
        lessons=lessons,
        kb_func=kb_func,
        pattern=CALLBACK_LECTURER_LESSON_PREFIX,
        update=update,
        context=context,
    )
    return StartHandlerState.START

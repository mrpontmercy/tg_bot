import logging
import sqlite3
from typing import Callable

from telegram import ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from config import (
    CALLBACK_LESSON_PREFIX,
    CALLBACK_USER_LESSON_PREFIX,
)

from handlers.start import get_current_keyboard
from handlers.login_decorators.login_required import lecturer_required
from services.db import get_user_by_tg_id
from services.exceptions import LessonError, SubscriptionError, UserError
from services.kb import (
    get_back_kb,
    get_flip_with_cancel_INLINEKB,
    get_lesson_INLINEKB,
    get_retry_or_back_keyboard,
)
from services.lesson import (
    calculate_timedelta,
    get_user_subscription,
    get_available_upcoming_lessons_from_db,
    get_user_upcoming_lessons,
    get_lessons_button,
    process_sub_to_lesson,
    update_info_after_cancel_lesson,
)
from handlers.login_decorators.login_required import user_required
from services.notification import notify_lecturer_user_cancel_lesson
from services.reply_text import send_error_message
from services.response import edit_callbackquery
from services.states import END, FlipKBState, StartHandlerState
from services.templates import render_template
from services.utils import Lesson


@user_required(StartHandlerState.SELECTING_ACTION)
async def show_my_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображать уроки, на которые записан пользователь

    узнать есть ли пользователь в бд
    узнать есть ли у него уроки
    """
    query = update.callback_query
    await query.answer()
    user_tg_id = update.effective_user.id

    user = await get_user_by_tg_id(user_tg_id)

    context.user_data["curr_user_tg_id"] = user.telegram_id

    try:
        lessons_by_user = await get_user_upcoming_lessons(user.id)
    except LessonError as e:
        kb = await get_current_keyboard(update)
        await edit_callbackquery(query, "error.jinja", err=str(e), keyboard=kb)
        # await context.bot.send_message(user_tg_id, str(e), reply_markup=kb)
        return StartHandlerState.SELECTING_ACTION

    first_lesson: Lesson = lessons_by_user[0]
    context.user_data["curr_lesson"] = first_lesson
    kb = get_flip_with_cancel_INLINEKB(
        0, len(lessons_by_user), CALLBACK_USER_LESSON_PREFIX
    )
    await context.bot.send_message(
        user_tg_id,
        render_template("lesson.jinja", data=first_lesson.to_dict_lesson_info()),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )
    return StartHandlerState.SELECTING_ACTION


@user_required(StartHandlerState.SELECTING_ACTION)
async def show_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Получить список всех доступных уроков, на которые пользователь еще не записан! (сортировать по дате начала занятия)
    Отобразить первый урок, добавить клавиатуру
    """
    callbackquery = update.callback_query
    await callbackquery.answer()

    user_tg_id = update.effective_user.id

    user = await get_user_by_tg_id(user_tg_id)

    context.user_data["curr_user_tg_id"] = user.telegram_id

    try:
        lessons = await get_available_upcoming_lessons_from_db(user.id)
    except LessonError as e:
        kb = await get_current_keyboard(update)
        await callbackquery.edit_message_text(str(e), reply_markup=kb)
        return StartHandlerState.SELECTING_ACTION

    context.user_data["curr_lesson"] = lessons[0]
    kb = get_lesson_INLINEKB(0, len(lessons), CALLBACK_LESSON_PREFIX)
    await edit_callbackquery(
        callbackquery,
        "lesson.jinja",
        data=lessons[0].to_dict_lesson_info(),
        keyboard=kb,
    )

    return FlipKBState.START


# func = user_required(state)(lecturer_required(state)(func))
@user_required(StartHandlerState.SELECTING_ACTION)
async def cancel_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    отменять не поздее чем за 2 часа до занятия

    Обновить информацию в таблице lesson
    обновить количество уроков в абонименте
    удалить строчку из user_lesson
    """
    user_tg_id = context.user_data.get("curr_user_tg_id")
    if user_tg_id is None:
        await update.callback_query.edit_message_text(
            "Вы не записаны ни на одно занятие!"
        )
        return StartHandlerState.SELECTING_ACTION

    lesson: Lesson | None = context.user_data.get("curr_lesson")
    if lesson is None:
        await update.callback_query.edit_message_text(
            "Не удалось удалить урок, попробуйте снова!"
        )
        return StartHandlerState.SELECTING_ACTION

    before_lesson_time = calculate_timedelta(lesson.time_start)

    if before_lesson_time.total_seconds() // 3600 < 2:
        await update.callback_query.edit_message_text(
            "До занятия осталось меньше 2х часов. Отменить занятие не получится"
        )
        return StartHandlerState.SELECTING_ACTION

    user = await get_user_by_tg_id(user_tg_id)
    try:
        await update_info_after_cancel_lesson(lesson, user)
    except SubscriptionError as e:
        await send_error_message(user_tg_id, context, err=str(e))
        return StartHandlerState.SELECTING_ACTION
    except sqlite3.Error as e:
        logging.getLogger(__name__).exception(e)
        await update.callback_query.edit_message_text(
            "Что-то пошло не так, не удалось записаться на занятие.\nОбратитесь к администратору!"
        )
        return StartHandlerState.SELECTING_ACTION

    lecturer_id = lesson.lecturer_id
    await notify_lecturer_user_cancel_lesson(
        f"{user.f_name} {user.s_name}", lecturer_id, lesson, context
    )
    await update.callback_query.edit_message_text("Занятие успешно отменено!")
    return StartHandlerState.SELECTING_ACTION


async def user_lessons_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lessons, state = await get_lessons_button(
        update,
        context,
        get_user_upcoming_lessons,
        StartHandlerState.SELECTING_ACTION,
    )

    if lessons is None:
        return state

    kb_func = get_flip_with_cancel_INLINEKB
    await _lessons_button(
        lessons=lessons,
        kb_func=kb_func,
        pattern=CALLBACK_USER_LESSON_PREFIX,
        update=update,
        context=context,
    )
    return StartHandlerState.SELECTING_ACTION


async def available_lessons_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lessons, end_state = await get_lessons_button(
        update,
        context,
        get_available_upcoming_lessons_from_db,
        FlipKBState.START,
    )
    if lessons is None:
        return end_state

    kb_func = get_lesson_INLINEKB
    await _lessons_button(lessons, kb_func, CALLBACK_LESSON_PREFIX, update, context)
    return FlipKBState.START


async def _lessons_button(
    lessons: list[Lesson],
    kb_func: Callable,
    pattern: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Ответить на колбекквери (чтобы кнопка не отображалась нажатой)
    Получаем список всех уроков
    Формируем новую клавиатуру
    """
    query = update.callback_query
    await query.answer()
    current_index = int(query.data[len(pattern) :])
    context.user_data["curr_lesson"] = lessons[current_index]
    kb = kb_func(current_index, len(lessons), pattern)
    await query.edit_message_text(
        render_template(
            "lesson.jinja", data=lessons[current_index].to_dict_lesson_info()
        ),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )


async def subscribe_to_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Узнаем, зарегестрирован ли текущий пользователь (если нет отправляем регистрироваться)
    Узнаем есть ли у пользователя подписка (если есть, то узнать сколько занятий осталось)(если нету, предложить оформить)
    ОБновляем значение оставшихся занятий у пользователя
    Уменьшаем количество доступных мест у занятия
    Записываем в M2M информацию о пользователе и занятии
    """
    query = update.callback_query
    await query.answer()
    user_tg_id = update.effective_user.id
    back_kb = get_back_kb(END)
    try:
        user = await get_user_by_tg_id(user_tg_id)
        sub_by_user_id = await get_user_subscription(user.id)
        curr_lesson = context.user_data.get("curr_lesson")
        await process_sub_to_lesson(curr_lesson, sub_by_user_id)
        if curr_lesson is None:
            await query.edit_message_text("Что-то пошло не так!", reply_markup=back_kb)
            return StartHandlerState.SHOWING
    except (UserError, SubscriptionError, LessonError) as err:
        await edit_callbackquery(query, "error.jinja", err=str(err), keyboard=back_kb)
        return StartHandlerState.SHOWING
    except sqlite3.Error as e:
        logging.getLogger(__name__).exception(e)
        await query.edit_message_text(
            "Что-то пошло не так, не удалось записаться на занятие.\nОбратитесь к администратору!",
            reply_markup=back_kb,
        )
        return StartHandlerState.SHOWING

    del context.user_data["curr_lesson"]
    await query.edit_message_text("Вы успешно записались на занятие!")
    context.user_data["START_OVER"] = True
    return ConversationHandler.END

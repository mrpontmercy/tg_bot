from datetime import datetime, timedelta, timezone
import logging
import sqlite3
from typing import Callable

from telegram import ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from config import (
    CALLBACK_LESSON_PREFIX,
    CALLBACK_USER_LESSON_PREFIX,
    DATETIME_FORMAT,
)

from services.db import get_user
from services.exceptions import LessonError, SubscriptionError, UserError
from services.kb import (
    KB_START_COMMAND_REGISTERED,
    get_flip_with_cancel_INLINEKB,
    get_lesson_INLINEKB,
)
from services.lesson import (
    calculate_timedelta,
    check_user_in_db,
    get_user_subscription,
    get_available_lessons_from_db,
    get_user_lessons,
    process_sub_to_lesson,
    update_info_after_cancel_lesson,
)
from services.states import StartHandlerStates
from services.templates import render_template
from services.utils import Lesson


async def show_my_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображать уроки, на которые записан пользователь

    узнать есть ли пользователь в бд
    узнать есть ли у него уроки
    """

    user_tg_id = update.effective_user.id

    user = await get_user(user_tg_id)

    if user is None:
        await update.message.reply_text("Пользователь не зарегестрирован!")
        return StartHandlerStates.START

    context.user_data["curr_user_tg_id"] = user.telegram_id

    try:
        lessons_by_user = await get_user_lessons(user.id)
    except LessonError as e:
        await context.bot.send_message(
            user_tg_id, str(e), reply_markup=KB_START_COMMAND_REGISTERED
        )
        return StartHandlerStates.START
    first_lesson: Lesson = lessons_by_user[0]
    context.user_data["curr_lesson"] = first_lesson
    kb = get_flip_with_cancel_INLINEKB(
        0, len(lessons_by_user), CALLBACK_USER_LESSON_PREFIX
    )
    await context.bot.send_message(
        user_tg_id,
        render_template("lesson.jinja", first_lesson.to_dict_lesson_info()),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )
    return StartHandlerStates.START


async def show_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Получить список всех доступных уроков, на которые пользователь еще не записан! (сортировать по дате начала занятия)
    Отобразить первый урок, добавить клавиатуру
    """

    user_tg_id = update.effective_user.id

    user = await get_user(user_tg_id)

    if user is None:
        await update.message.reply_text("Пользователь не зарегестрирован!")
        return StartHandlerStates.START

    context.user_data["curr_user_tg_id"] = user.telegram_id

    try:
        lessons = await get_available_lessons_from_db(user.id)
    except LessonError as e:
        await context.bot.send_message(
            user_tg_id, str(e), reply_markup=KB_START_COMMAND_REGISTERED
        )
        return StartHandlerStates.START

    context.user_data["curr_lesson"] = lessons[0]
    kb = get_lesson_INLINEKB(0, len(lessons), CALLBACK_LESSON_PREFIX)
    await context.bot.send_message(
        update.effective_chat.id,
        text=render_template("lesson.jinja", data=lessons[0].to_dict_lesson_info()),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )

    return StartHandlerStates.START


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
        return StartHandlerStates.START
    lesson: Lesson | None = context.user_data.get("curr_lesson")
    if lesson is None:
        await update.message.reply_text("Не удалось удалить урок, попробуйте снова!")
        return StartHandlerStates.START

    before_lesson_time = calculate_timedelta(lesson.time_start)
    if before_lesson_time.seconds // 3600 < 2:
        await update.message.reply_text(
            "До занятия осталось меньше 2х часов. Отменить занятие не получится"
        )
        return StartHandlerStates.START

    try:
        user = await get_user(user_tg_id)
        await update_info_after_cancel_lesson(lesson, user)
    except (SubscriptionError, UserError) as e:
        await update.message.reply_text(str(e))
        return StartHandlerStates.START
    except sqlite3.Error as e:
        logging.getLogger(__name__).exception(e)
        await update.callback_query.edit_message_text(
            "Что-то пошло не так, не удалось записаться на занятие.\nОбратитесь к администратору!"
        )
        return StartHandlerStates.START
    await update.callback_query.edit_message_text("Занятие успешно отменено!")
    return StartHandlerStates.START


async def user_lessons_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg_id = context.user_data.get("curr_user_tg_id")
    if user_tg_id is None:
        await update.callback_query.edit_message_text(
            "Вы не записаны ни на одно занятие!"
        )
        return StartHandlerStates.START

    try:
        user = await get_user(user_tg_id)
        lessons_by_user = await get_user_lessons(user.id)
    except (LessonError, UserError) as e:
        logging.getLogger(__name__).exception(e)
        await update.callback_query.edit_message_text(str(e))
        return StartHandlerStates.START

    kb_func = get_flip_with_cancel_INLINEKB
    await _lessons_button(
        lessons=lessons_by_user,
        kb_func=kb_func,
        pattern=CALLBACK_USER_LESSON_PREFIX,
        update=update,
        context=context,
    )
    return StartHandlerStates.START


async def available_lessons_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg_id = context.user_data.get("curr_user_tg_id")
    if user_tg_id is None:
        await update.callback_query.edit_message_text(
            "Вы не записаны ни на одно занятие!"
        )
        return StartHandlerStates.START
    try:
        user = await get_user(user_tg_id)
        lessons = await get_available_lessons_from_db(user.id)
    except (LessonError, UserError) as e:
        logging.getLogger(__name__).exception(e)
        await update.callback_query.edit_message_text(str(e))
        return StartHandlerStates.START

    kb_func = get_lesson_INLINEKB
    await _lessons_button(lessons, kb_func, CALLBACK_LESSON_PREFIX, update, context)
    return StartHandlerStates.START


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
        render_template("lesson.jinja", lessons[current_index].to_dict_lesson_info()),
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
    try:
        user = await get_user(user_tg_id)
    except UserError:
        await query.edit_message_text(
            "Что-то пошло не так. Возможная ошибка\n\n" + str(e)
        )
        return ConversationHandler.END

    curr_lesson = context.user_data.get("curr_lesson")
    if curr_lesson is None:
        await query.edit_message_text(
            "Что-то пошло не так!", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    del context.user_data["curr_lesson"]

    try:
        sub_by_user_id = await get_user_subscription(user.id)
    except SubscriptionError as e:
        await query.edit_message_text(str(e))
        return ConversationHandler.END

    try:
        await process_sub_to_lesson(curr_lesson, sub_by_user_id)
    except LessonError as e:
        await query.edit_message_text(str(e))
        return ConversationHandler.END
    except sqlite3.Error as e:
        logging.getLogger(__name__).exception(e)
        await query.edit_message_text(
            "Что-то пошло не так, не удалось записаться на занятие.\nОбратитесь к администратору!"
        )
        return ConversationHandler.END

    await query.edit_message_text("Вы успешно записались на занятие!")
    return ConversationHandler.END

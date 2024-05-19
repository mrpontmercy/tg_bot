from datetime import datetime, timedelta, timezone
import logging
import sqlite3

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import (
    CALLBACK_LESSON_PATTERN,
    CALLBACK_USER_LESSON_PATTERN,
    DATETIME_FORMAT,
)
from db import get_db
from services.db import get_user
from services.exceptions import LessonError, SubscriptionError, UserError
from services.kb import get_flip_with_cancel_INLINEKB, get_lesson_INLINEKB
from services.lesson import (
    check_user_in_db,
    get_user_subscription,
    get_available_lessons_from_db,
    get_user_lessons,
    process_sub_to_lesson,
    update_info_after_cancel_lesson,
)
from services.templates import render_template
from services.utils import Lesson


async def show_my_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображать уроки, на которые записан пользователь

    узнать есть ли пользователь в бд
    узнать есть ли у него уроки
    """

    user_tg_id = update.effective_user.id
    try:
        user = await get_user(user_tg_id)
    except UserError as e:
        return await update.effective_message.reply_text(
            e + "\nСперва нужно зарегестрироваться!"
        )
    context.user_data["curr_user"] = user

    try:
        lessons_by_user = await get_user_lessons(user.id)
    except LessonError as e:
        return await update.message.reply_text(e)
    first_lesson: Lesson = lessons_by_user[0]
    context.user_data["curr_lesson"] = first_lesson
    kb = get_flip_with_cancel_INLINEKB(
        0, len(lessons_by_user), CALLBACK_USER_LESSON_PATTERN
    )
    await update.message.reply_text(
        render_template("lesson.jinja", first_lesson.to_dict_lesson_info()),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )


async def show_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Получить список всех доступных уроков, на которые пользователь еще не записан! (сортировать по дате начала занятия)
    Отобразить первый урок, добавить клавиатуру
    """
    try:
        lessons = await get_available_lessons_from_db()
    except LessonError as e:
        return await update.effective_message.reply_text(e)

    context.user_data["curr_lesson"] = lessons[0]
    kb = get_lesson_INLINEKB(0, len(lessons), CALLBACK_LESSON_PATTERN)
    await context.bot.send_message(
        update.effective_chat.id,
        text=render_template("lesson.jinja", data=lessons[0].to_dict_lesson_info()),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )


async def cancel_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    отменять не поздее чем за 2 часа до занятия

    Обновить информацию в таблице lesson
    обновить количество уроков в абонименте
    удалить строчку из user_lesson
    """
    user = context.user_data.get("curr_user")
    if user is None:
        return await update.callback_query.edit_message_text(
            "Вы не записаны ни на одно занятие!"
        )
    lesson: Lesson | None = context.user_data.get("curr_lesson")
    if lesson is None:
        await update.message.reply_text("Не удалось удалить урок, попробуйте снова!")
        return

    lesson_dt_utc = datetime.strptime(lesson.time_start, DATETIME_FORMAT) - timedelta(
        hours=4
    )
    user_dt_utc = datetime.now(timezone.utc)
    user_dt_utc = datetime(
        user_dt_utc.year,
        user_dt_utc.month,
        user_dt_utc.day,
        user_dt_utc.hour,
        user_dt_utc.minute,
    )
    diff_lesson_user_time = lesson_dt_utc - user_dt_utc
    if diff_lesson_user_time.seconds // 3600 < 2:
        return await update.message.reply_text(
            "До занятия осталось меньше 2х часов. Отменить занятие не получится"
        )

    try:
        await update_info_after_cancel_lesson(lesson, user)
    except SubscriptionError as e:
        return await update.message.reply_text(str(e))
    except sqlite3.Error as e:
        logging.getLogger(__name__).exception(e)
        return await update.callback_query.edit_message_text(
            "Что-то пошло не так, не удалось записаться на занятие.\nОбратитесь к администратору!"
        )
    await update.callback_query.edit_message_text("Занятие успешно отменено!")


async def user_lessons_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = context.user_data.get("curr_user")
    if user is None:
        return await update.callback_query.edit_message_text(
            "Вы не записаны ни на одно занятие!"
        )

    try:
        lessons_by_user = await get_user_lessons(user.id)
    except LessonError as e:
        return await update.callback_query.edit_message_text(e)

    kb_func = get_flip_with_cancel_INLINEKB
    await _lessons_button(
        lessons=lessons_by_user,
        kb_func=kb_func,
        pattern=CALLBACK_USER_LESSON_PATTERN,
        update=update,
        context=context,
    )


async def available_lessons_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lessons = await get_available_lessons_from_db()
    except LessonError as e:
        return await update.callback_query.edit_message_text(e)

    kb_func = get_lesson_INLINEKB
    await _lessons_button(lessons, kb_func, CALLBACK_LESSON_PATTERN, update, context)


async def _lessons_button(
    lessons, kb_func, pattern, update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Ответить на колбекквери (чтобы кнопка не отображалась нажатой)
    Получаем список всех уроков
    Формируем новую клавиатуру
    """
    query = update.callback_query
    await query.answer()

    print(query.data)
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
        curr_user_db = await check_user_in_db(user_tg_id)
    except UserError:
        return await query.edit_message_text(e + "\nПожалуйста, зарегестрируйтесь!")

    try:
        curr_lesson = context.user_data["curr_lesson"]
    except KeyError as e:
        logging.getLogger(__name__).exception(e)
        return await query.edit_message_text("Что-то пошло не так!")

    del context.user_data["curr_lesson"]

    try:
        sub_by_user_id = await get_user_subscription(curr_user_db.id)
    except SubscriptionError as e:
        return await query.edit_message_text(str(e))

    try:
        await process_sub_to_lesson(curr_lesson, sub_by_user_id)
    except LessonError as e:
        return await query.edit_message_text(str(e))
    except sqlite3.Error as e:
        logging.getLogger(__name__).exception(e)
        return await query.edit_message_text(
            "Что-то пошло не так, не удалось записаться на занятие.\nОбратитесь к администратору!"
        )

    await query.edit_message_text(
        "Вы успешно записались на занятие!", reply_markup=None
    )

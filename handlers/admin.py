import logging
import os
import sqlite3
import string

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import CALLBACK_SUB_PREFIX
from db import execute
from handlers.start import start_command
from services.admin import (
    delete_subscription,
    generate_sub_key,
    insert_lessons_into_db,
    save_file,
    update_user_to_lecturer,
    validate_num_of_classes,
    validate_phone_number,
    get_available_subs,
)
from services.db import get_user_by_phone_number
from services.exceptions import InputMessageError, SubscriptionError, UserError
from services.kb import (
    KB_ADMIN_COMMAND,
    get_flip_keyboard,
)
from services.lesson import get_lessons_from_file
from services.reply_text import send_error_message
from services.states import AdminStates
from services.templates import render_template
from services.utils import Subscription


unity = string.ascii_letters + string.digits


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = KB_ADMIN_COMMAND
    await update.message.reply_text(
        "Привет, в режиме АДМИНА можно создать ключ подписки. Нажми соответствующую кнопку!\n\nЧтобы прервать эту коману напиши: cancel или /cancel",
        reply_markup=kb,
    )
    return AdminStates.CHOOSING


async def enter_lecturer_phone_number(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text("Введите номер телефона преподователя!")
    return AdminStates.LECTURER_PHONE


async def make_lecturer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        phone_number = validate_phone_number(update.message.text)
    except InputMessageError as e:
        logging.getLogger(__name__).exception(e)
        await send_error_message(update.message.from_user.id, context, err=str(e))
        return AdminStates.LECTURER_PHONE

    try:
        user = await get_user_by_phone_number(phone_number)
    except UserError as e:
        await send_error_message(update.message.from_user.id, context, err=str(e))
        return AdminStates.LECTURER_PHONE

    try:
        await update_user_to_lecturer(user.id)
    except sqlite3.Error as e:
        logging.getLogger(__name__).exception(e)
        await update.message.reply_text("Что-то пошло не так!")
        return AdminStates.CHOOSING

    await update.message.reply_text(
        f"Пользователь с номером {phone_number} успешно обновлен до `Преподователь`",
        reply_markup=KB_ADMIN_COMMAND,
    )
    return AdminStates.CHOOSING


async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id
    await context.bot.send_message(
        chat_id, "Отправьте файл с уроками установленной формы.\n"
    )
    return AdminStates.GET_CSV_FILE


async def insert_into_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saved_file_path = await save_file(update.message.document, context)

    lessons = get_lessons_from_file(saved_file_path)
    if lessons is None:
        await send_error_message(
            update.effective_user.id,
            context,
            err="Неверно заполнен файл. Попробуй с другим файлом.",
        )
        os.remove(saved_file_path)
        return AdminStates.GET_CSV_FILE

    errors_after_inserting_lessons = await insert_lessons_into_db(lessons)

    if errors_after_inserting_lessons:
        await context.bot.send_message(
            update.message.from_user.id,
            "\n".join([row[0] for row in errors_after_inserting_lessons]),
        )

    os.remove(saved_file_path)
    err_lesson = "\n".join([row[-1] for row in errors_after_inserting_lessons])
    answer = f"Все уроки, кроме\n<b>{err_lesson}</b>\n были добавлены в общий список"
    await context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=answer,
        reply_markup=KB_ADMIN_COMMAND,
        parse_mode=ParseMode.HTML,
    )
    return AdminStates.CHOOSING


async def list_available_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        subs: list[Subscription] = await get_available_subs()
    except SubscriptionError as e:
        logging.getLogger(__name__).exception(e)
        await send_error_message(update.effective_user.id, context, err=str(e))
        return AdminStates.CHOOSING
    kb = get_flip_keyboard(0, len(subs), CALLBACK_SUB_PREFIX)
    sub = subs[0]
    print(f"{sub.sub_key=}")
    print(f"{sub.num_of_classes=}")
    context.user_data["sub_id"] = sub.id
    await context.bot.send_message(
        update.effective_user.id,
        text=render_template(
            "subs.jinja",
            data={"sub_key": sub.sub_key, "num_of_classes": sub.num_of_classes},
        ),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )


async def subs_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        subs = await get_available_subs()
    except SubscriptionError as e:
        logging.getLogger(__name__).exception(e)
        await query.edit_message_text(
            "Что-то пошло не так. Возможная ошибка\n\n" + str(e)
        )
        return AdminStates.CHOOSING

    current_index = int(query.data[len(CALLBACK_SUB_PREFIX) :])
    sub = subs[current_index]
    context.user_data["sub_id"] = sub.id
    await query.edit_message_text(
        text=render_template(
            "subs.jinja",
            data={
                "sub_key": sub.sub_key,
                "num_of_classes": sub.num_of_classes,
            },
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=get_flip_keyboard(current_index, len(subs), CALLBACK_SUB_PREFIX),
    )
    return AdminStates.CHOOSING


async def generate_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub_key = await generate_sub_key(20)

    context.user_data["sub_key"] = sub_key
    answer = f"Отлично, теперь введите количество уроков для подписки!"
    await update.effective_user.send_message(answer, reply_markup=KB_ADMIN_COMMAND)
    return AdminStates.NUM_OF_CLASSES


async def make_new_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        num_of_classes = validate_num_of_classes(update.message.text)
    except InputMessageError as e:
        logging.getLogger(__name__).exception(e)
        await update.message.reply_text(
            "Что-то пошло не так. Возможная ошибка:\n\n" + str(e)
        )
        return AdminStates.NUM_OF_CLASSES
    sub_key = context.user_data["sub_key"]
    del context.user_data["sub_key"]
    await execute(
        """insert into subscription (sub_key, num_of_classes) VALUES (:sub_key, :num_of_classes)""",
        {
            "sub_key": sub_key,
            "num_of_classes": num_of_classes,
        },
    )
    answer = (
        f"Подписка успешно создана:\n\nПолученный код нужно передать пользователю.\n"
        f"Код:\t{sub_key}\n\n"
    )
    await update.effective_message.reply_text(answer, reply_markup=KB_ADMIN_COMMAND)
    return AdminStates.CHOOSING


async def return_to_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)
    # await context.bot.send_message(
    #     update.message.from_user.id,
    #     render_template(template_name="start.jinja"),
    #     reply_markup=kb,
    #     parse_mode=ParseMode.HTML,
    # )
    return ConversationHandler.END


async def remove_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub_id: int | None = context.user_data.get("sub_id")
    if sub_id is None:
        await update.message.reply_text("Не удалось найти подписку!")
        return AdminStates.CHOOSING
    try:
        await delete_subscription(sub_id)
    except sqlite3.Error:
        raise

    await update.callback_query.edit_message_text("Абонемент удален!")
    return AdminStates.CHOOSING
    # await update.message.reply_text("Подписка удалена!")

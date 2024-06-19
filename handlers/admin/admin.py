import logging
import sqlite3
import string

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import CALLBACK_SUB_PREFIX
from db import execute
from handlers.start import start_command
from services.admin import (
    delete_subscription,
    generate_sub_key,
    process_insert_lesson_into_db,
    update_user_to_lecturer,
    validate_num_of_classes,
    validate_phone_number,
    get_available_subs,
)
from services.db import get_user_by_phone_number
from services.exceptions import InputMessageError, SubscriptionError, UserError
from services.kb import (
    KB_ADMIN_COMMAND,
    get_back_kb,
    get_flip_delete_back_keyboard,
    get_retry_or_back_keyboard,
)
from services.reply_text import send_error_message
from services.response import edit_callbackquery, send_message
from services.states import END, AdminState, FlipKBState
from services.templates import render_template
from services.utils import Subscription, add_start_over


unity = string.ascii_letters + string.digits


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    kb = KB_ADMIN_COMMAND
    await edit_callbackquery(query, "admin.jinja", keyboard=kb)
    return AdminState.CHOOSING


async def enter_lecturer_phone_number(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    await context.bot.send_message(tg_id, "Введите номер телефона преподователя!")
    return AdminState.LECTURER_PHONE


async def make_lecturer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = get_retry_or_back_keyboard(AdminState.ADD_LECTURER, AdminState.START_ADMIN)
    tg_id = update.effective_user.id
    try:
        phone_number = validate_phone_number(update.message.text)
    except InputMessageError as e:
        await send_error_message(
            update.message.from_user.id, context, err=str(e), keyboard=kb
        )
        return AdminState.CHOOSING

    try:
        user = await get_user_by_phone_number(phone_number)
    except UserError as e:
        await send_error_message(
            update.message.from_user.id, context, err=str(e), keyboard=kb
        )
        return AdminState.CHOOSING

    try:
        await update_user_to_lecturer(user.id)
    except sqlite3.Error as e:
        logging.getLogger(__name__).exception(e)
        await send_error_message(tg_id, context, err="Что-то пошло не так!", keyboard=kb)
        return AdminState.CHOOSING
    back_kb = get_back_kb(AdminState.START_ADMIN)
    await update.message.reply_text(
        f"Пользователь с номером {phone_number} успешно обновлен до `Преподователь`",
        reply_markup=back_kb,
    )
    return AdminState.CHOOSING


async def send_lessons_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id
    await context.bot.send_message(
        chat_id, "Отправьте файл с уроками установленной формы.\n"
    )
    return AdminState.GET_CSV_FILE


async def insert_lesson_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rec_document = update.message.document
    user_tg_id = update.effective_user.id
    if await process_insert_lesson_into_db(rec_document, user_tg_id, context):
        return AdminState.CHOOSING
    else:
        return AdminState.GET_CSV_FILE

    # if state is None:
    #     await context.bot.send_message(
    #         chat_id=user_tg_id,
    #         text="Что-то пошло не так",
    #         reply_markup=KB_ADMIN_COMMAND,
    #         parse_mode=ParseMode.HTML,
    #     )
    #     return AdminState.CHOOSING
    # return state


async def list_available_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    back_kb = get_back_kb(AdminState.START_ADMIN)
    try:
        subs: list[Subscription] = await get_available_subs()
    except SubscriptionError as e:
        await edit_callbackquery(query, "error.jinja", err=str(e), keyboard=back_kb)
        return END
    kb = get_flip_delete_back_keyboard(0, len(subs), CALLBACK_SUB_PREFIX)
    sub = subs[0]
    context.user_data["sub_id"] = sub.id
    await query.edit_message_text(
        text=render_template(
            "subs.jinja",
            data={"sub_key": sub.sub_key, "num_of_classes": sub.num_of_classes},
        ),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )
    return FlipKBState.START


async def subs_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    back_kb = get_back_kb(END)
    try:
        subs = await get_available_subs()
    except SubscriptionError as e:
        await edit_callbackquery(query, "error.jinja", err=str(e), keyboard=back_kb)
        # await query.edit_message_text(
        #     "Что-то пошло не так. Возможная ошибка\n\n" + str(e)
        # )
        return FlipKBState.START

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
        reply_markup=get_flip_delete_back_keyboard(
            current_index, len(subs), CALLBACK_SUB_PREFIX
        ),
    )
    return FlipKBState.START


async def generate_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sub_key = await generate_sub_key(20)

    context.user_data["sub_key"] = sub_key
    back_kb = get_back_kb(AdminState.START_ADMIN)
    answer = f"Отлично, теперь введите количество уроков для подписки!"
    await query.edit_message_text(answer, reply_markup=back_kb)

    return AdminState.GET_NUM_OF_CLASSES


@add_start_over
async def make_new_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = get_retry_or_back_keyboard(AdminState.GENERATE_SUB, AdminState.START_ADMIN)
    tg_id = update.effective_user.id

    try:
        num_of_classes = validate_num_of_classes(update.message.text)
    except InputMessageError as e:
        await send_error_message(
            tg_id,
            context,
            err=str(e),
            keyboard=kb,
        )
        return AdminState.CHOOSING
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
    return AdminState.CHOOSING


async def return_to_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()

    await start_command(update, context)
    # await context.bot.send_message(
    #     update.message.from_user.id,
    #     render_template(template_name="start.jinja"),
    #     reply_markup=kb,
    #     parse_mode=ParseMode.HTML,
    # )
    return ConversationHandler.END


async def remove_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    sub_id: int | None = context.user_data.get("sub_id")
    back_kb = get_back_kb(AdminState.START_ADMIN)
    if sub_id is None:
        await send_error_message(
            tg_id, context, err="Не удалось найти подписку!", keyboard=back_kb
        )
        return AdminState.CHOOSING
    try:
        await delete_subscription(sub_id)
    except sqlite3.Error:
        await send_error_message(
            tg_id,
            context,
            err="Не удалось удалить подписку! Обратитесь к администратору",
            keyboard=back_kb,
        )
        return AdminState.CHOOSING

    back_kb = get_back_kb(AdminState.LIST_AVAILABLE_SUBS)
    await update.callback_query.edit_message_text(
        "Абонемент удален!", reply_markup=back_kb
    )
    return AdminState.CHOOSING
    # await update.message.reply_text("Подписка удалена!")


async def end_admin_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["START_OVER"] = True
    await start_command(update, context)
    return END

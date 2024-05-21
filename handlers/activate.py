import logging
import sqlite3
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from services.activate import activate_key, validate_args
from services.exceptions import (
    InputMessageError,
    InvalidSubKey,
    SubscriptionError,
    UserError,
)
from services.db import get_user
from services.lesson import get_user_subscription
from services.states import StartHandlerStates
from services.templates import render_template

logger = logging.getLogger(__name__)


async def activate_key_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        user = await get_user(update.effective_user.id)
    except UserError as e:
        logger.exception(e)
        await update.message.reply_text(
            "Что-то пошло не так. Возможная ошибка\n\n" + str(e),
            parse_mode=ParseMode.HTML,
        )
        return

    await update.message.reply_text("Отправьте ключ абонимента!")
    context.user_data["curr_user_tg_id"] = user.telegram_id
    return StartHandlerStates.ACTIVATE_KEY


async def register_sub_key_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mess_args = update.message.text.split(" ")

    try:
        args = validate_args(mess_args)
    except InputMessageError as e:
        logger.exception(e)
        await update.effective_message.reply_text(
            render_template("error.jinja", err=str(e)), parse_mode=ParseMode.HTML
        )
        return StartHandlerStates.ACTIVATE_KEY

    sub_key = args[0]
    user_tg_id = context.user_data.get("curr_user_tg_id")
    if user_tg_id is None:
        await update.message.reply_text(render_template("error.jinja", err=str(e)))
        return ConversationHandler.END
    del context.user_data["curr_user_tg_id"]
    try:
        user = await get_user(user_tg_id)
        final_message = await activate_key(sub_key, user)
    except (InvalidSubKey, UserError) as e:
        logger.exception(e)
        await update.effective_message.reply_text(
            render_template("error.jinja", err=str(e)), parse_mode=ParseMode.HTML
        )
        return StartHandlerStates.ACTIVATE_KEY
    except sqlite3.OperationalError as e:
        logger.exception(e)
        await update.effective_message.reply_text(
            render_template("error.jinja", err=str(e)), parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    await update.effective_message.reply_text(final_message)

    return ConversationHandler.END


async def show_number_of_remaining_classes_on_subscription(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user = await get_user(update.message.from_user.id)
    try:
        subscription = await get_user_subscription(user_db_id=user.id)
    except SubscriptionError as e:
        logger.exception(e)
        await update.message.reply_text(str(e))
        return StartHandlerStates.START
    await update.effective_message.reply_text(
        f"У вас осталось {subscription.num_of_classes} занятий на абонименте"
    )
    return StartHandlerStates.START
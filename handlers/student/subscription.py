import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from services.subscription import activate_key, validate_args
from services.exceptions import (
    InputMessageError,
    InvalidSubKey,
    SubscriptionError,
    UserError,
)
from services.db import get_user_by_tg_id
from services.lesson import get_user_subscription
from services.reply_text import send_error_message
from services.states import StartHandlerState

logger = logging.getLogger(__name__)


async def activate_subkey_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_tg_id = update.effective_user.id
    try:
        user = await get_user_by_tg_id(update.effective_user.id)
    except UserError as e:
        logger.exception(e)
        await send_error_message(user_tg_id, context, err=str(e))
        return

    await update.message.reply_text("Отправьте ключ абонимента!")
    context.user_data["curr_user_tg_id"] = user.telegram_id
    return StartHandlerState.ACTIVATE_KEY


async def register_sub_key_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mess_args = update.message.text.split(" ")
    user_tg_id = context.user_data.get("curr_user_tg_id")

    try:
        args = validate_args(mess_args)
    except InputMessageError as e:
        logger.exception(e)
        await send_error_message(user_tg_id, context, err=str(e))
        return StartHandlerState.ACTIVATE_KEY

    sub_key = args[0]
    if user_tg_id is None:
        await send_error_message(user_tg_id, context, err=str(e))
        return ConversationHandler.END
    del context.user_data["curr_user_tg_id"]
    try:
        user = await get_user_by_tg_id(user_tg_id)
        final_message = await activate_key(sub_key, user)
    except (InvalidSubKey, UserError) as e:
        logger.exception(e)
        await send_error_message(user_tg_id, context, err=str(e))
        return StartHandlerState.ACTIVATE_KEY
    except sqlite3.Error as e:
        logger.exception(e)
        await send_error_message(
            user_tg_id, context, err="Не удалось выполнить операцию."
        )
        return StartHandlerState.START

    await update.effective_message.reply_text(final_message)

    return StartHandlerState.START


async def show_number_of_remaining_classes_on_subscription(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user = await get_user_by_tg_id(update.message.from_user.id)
    try:
        subscription = await get_user_subscription(user_db_id=user.id)
    except SubscriptionError as e:
        logger.exception(e)
        await send_error_message(update.message.from_user.id, context, err=str(e))
        return StartHandlerState.START
    await context.bot.send_message(
        user.telegram_id,
        f"У вас осталось {subscription.num_of_classes} занятий на абонименте",
    )
    return StartHandlerState.START

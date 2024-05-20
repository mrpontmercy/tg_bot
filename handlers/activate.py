import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from handlers.start import ACTIVATE_KEY, START
from services.activate import activate_key, validate_args
from services.exceptions import (
    ErrorContextArgs,
    InvalidSubKey,
    SubscriptionError,
    UserError,
)
from services.db import get_user
from services.lesson import get_user_subscription
from services.utils import UserID

logger = logging.getLogger(__name__)


async def activate_key_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = await get_user(update.effective_user.id)

    if user is None:
        await update.message.reply_text("Пользователь не зарегестрирован!")
        return ConversationHandler.END

    await update.message.reply_text("Отправьте ключ абонимента!")
    context.user_data["curr_user"] = user
    return ACTIVATE_KEY


async def register_sub_key_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mess_args = update.message.text.split(" ")

    try:
        args = validate_args(mess_args)
    except ErrorContextArgs as e:
        logger.exception(e)
        await update.effective_message.reply_text(str(e))
        return ACTIVATE_KEY

    sub_key = args[0]
    user = context.user_data.get("curr_user")
    if user is None:
        await update.message.reply_text(
            "Что-то пошло не так, попробуйте с самого начала.\n\n/start"
        )
        return ConversationHandler.END
    del context.user_data["curr_user"]
    try:
        final_message = await activate_key(sub_key, user)
    except InvalidSubKey as e:
        await update.effective_message.reply_text(str(e))
        return ACTIVATE_KEY
    except sqlite3.OperationalError as e:
        logger.exception(e)
        await update.effective_message.reply_text(
            "Что-то пошло не так. Скорее всего пока данная команда не работает!"
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
        return START
    await update.effective_message.reply_text(
        f"У вас осталось {subscription.num_of_classes} занятий на абонименте"
    )
    return START

import logging
import sqlite3
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler
from handlers.start import ACTIVATE_KEY
from services.activate import activate_key, validate_args
from services.exceptions import ErrorContextArgs, InvalidSubKey, UserError
from services.db import get_user

logger = logging.getLogger(__name__)


async def activate_key_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    try:
        user = await get_user(update.effective_user.id)
    except UserError as e:
        logger.exception(e)
        return await update.effective_message.reply_text(e)

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

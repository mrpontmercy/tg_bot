import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes
from services.activate import activate_key, get_user, validate_args
from services.exceptions import ErrorContextArgs, UserError

logger = logging.getLogger(__name__)


async def activate_key_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        args = validate_args(context.args)
    except ErrorContextArgs as e:
        logger.exception(e)
        return await update.effective_message.reply_text(
            "Некоректный ключ. Пропробуйте другой!"
        )

    try:
        user = await get_user(update.effective_user.id)
    except UserError as e:
        logger.exception(e)
        return await update.effective_message.reply_text(e)

    sub_key: str = args[0]
    try:
        final_message = await activate_key(sub_key, user)
    except sqlite3.OperationalError as e:
        logger.exception(e)
        return await update.edited_message.reply_text(
            "Что-то пошло не так. Скорее всего пока данная команда не работает!"
        )
    return await update.effective_message.reply_text(final_message)

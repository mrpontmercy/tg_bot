import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from all_strings import GREETINGS
from handlers.start import get_current_keyboard
from services.register import (
    insert_user,
    validate_message,
)

REGISTER = 1

logger = logging.getLogger(__name__)


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, GREETINGS)
    return REGISTER


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    full_info = [user.id, user.username] + update.effective_message.text.split(" ")
    try:
        validated_message = validate_message(full_info)
    except Exception as e:
        logger.exception(e)
        await update.effective_message.reply_text(
            "Ошибка в данных, попробуйте снова. Возможная ошибка:\n\n" + str(e)
        )
        return REGISTER

    params = validated_message.to_dict()
    try:
        await insert_user(params)
    except sqlite3.Error as e:
        logger.exception(e)
        await context.bot.send_message(
            user.id,
            "Произошла ошибка.\nНачните регистрацию заново",
        )
        return REGISTER
    kb = await get_current_keyboard(update)
    await context.bot.send_message(
        user.id, "Вы успешно зарегестрировались!", reply_markup=kb
    )

    return ConversationHandler.END

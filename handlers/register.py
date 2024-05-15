import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from all_strings import GREETINGS
from db import close_db, execute, get_db
from services.register import (
    ValidationEmailError,
    ValidationFirstNameError,
    ValidationPhoneNumberError,
    ValidationSecondNameError,
    ValidationUserError,
    validate_user,
)

REGISTER = 1

logger = logging.getLogger(__name__)


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, GREETINGS)
    return REGISTER


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id
    answer = update.message.text.split()

    try:
        answer = validate_user(answer)
    except (
        ValidationFirstNameError,
        ValidationSecondNameError,
        ValidationUserError,
        ValidationPhoneNumberError,
        ValidationEmailError,
    ) as e:
        logger.exception(e)
        await context.bot.send_message(chat_id, "Ошибка в данных, попробуйте")
        return

    params = {
        "telegram_id": update.effective_user.id,
        "username": update.effective_user.username,
        "f_name": answer[0],
        "s_name": answer[1],
        "phone_number": answer[2],
        "email": answer[3],
    }
    try:
        await execute(
            """INSERT INTO users (telegram_id, username, f_name, s_name, phone_number, email) 
                VALUES (:telegram_id, :username, :f_name, :s_name, :phone_number, :email)""",
            params,
        )
    except Exception as e:
        logger.exception(e)
        await context.bot.send_message(
            chat_id,
            "Произошла ошибка.\nНачните регистрацию заново: /register",
        )
        return ConversationHandler.END

    await context.bot.send_message(chat_id, "Вы успешно зарегестрировались!")

    return ConversationHandler.END


async def canlec_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Регистрация отменена")
    return ConversationHandler.END

import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes
from handlers.create_conv_handler import return_back_start
from handlers.start import get_current_keyboard, start_command
from services.register import (
    insert_user,
    validate_message,
)
from services.response import send_message
from services.states import END, RegisterState, StartHandlerState
from services.templates import render_template

logger = logging.getLogger(__name__)


async def start_register_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    chat_id = update.effective_chat.id
    await send_message(chat_id, "register_example.jinja", context)

    return RegisterState.REGISTER


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
        return RegisterState.REGISTER

    params = validated_message.to_dict()
    try:
        await insert_user(params)
    except sqlite3.Error as e:
        logger.exception(e)
        await context.bot.send_message(
            user.id,
            "Произошла ошибка.\nНачните регистрацию заново",
        )
        return RegisterState.REGISTER
    kb = await get_current_keyboard(update)
    await context.bot.send_message(user.id, "Вы успешно зарегестрировались!")
    return return_back_start(update, context)


# async def stop_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.effective_user.send_message("Операция приостановлена!")
#     context.user_data["START_OVER"] = True
#     await start_command(update, context)
#     return END

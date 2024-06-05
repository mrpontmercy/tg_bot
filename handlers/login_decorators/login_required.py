from config import LECTURER_STATUS
from handlers.start import start_command
from services.db import get_user_by_tg_id
from services.exceptions import UserError
from services.reply_text import send_error_message


from telegram import Update
from telegram.ext import ContextTypes


import functools
import logging


def lecturer_required(state):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_tg_id = update.effective_user.id
            status = context.user_data.get("curr_user_status")
            if status and status == LECTURER_STATUS:
                return await func(update, context)
            else:
                logging.getLogger(__name__).exception(
                    f"{func.__module__}::{func.__name__} - error \n"
                    + f"Пользователь {user_tg_id=} не является преподавателем"
                )
                await send_error_message(
                    user_tg_id, context, err="Пользователь не является преподавателем"
                )
                return state

        return wrapper

    return decorator


def user_required(state):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_tg_id = update.effective_user.id
            try:
                user = await get_user_by_tg_id(user_tg_id)
            except UserError as e:
                logging.getLogger(__name__).exception(
                    f"{func.__module__}::{func.__name__} - error \n" + str(e)
                )
                await send_error_message(user_tg_id, context, err=str(e))
                await start_command(update, context)
                return state
            context.user_data["curr_user_status"] = user.status
            return await func(update, context)

        return wrapper

    return decorator

import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, filters

from config import LECTURER_STATUS
from services.db import get_user_by_tg_id
from services.exceptions import UserError
from services.filters import ADMIN_FILTER, is_admin
from services.kb import (
    KB_START_COMMAND,
    KB_START_COMMAND_ADMIN,
    KB_START_COMMAND_REGISTERED,
    KB_START_COMMAND_REGISTERED_ADMIN,
    KB_START_COMMAND_REGISTERED_LECTURER,
    KB_START_COMMAND_REGISTERED_LECTURER_ADMIN,
)
from services.states import END, StartHandlerState
from services.templates import render_template


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # await update.message.edit_reply_markup(reply_markup=ReplyKeyboardRemove())
    kb = await get_current_keyboard(update)
    always_display_text = render_template("start_choose_form.jinja")
    if context.user_data.get("START_OVER"):
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                always_display_text, reply_markup=kb
            )
        else:
            await context.bot.send_message(
                update.effective_user.id, always_display_text, reply_markup=kb
            )
    else:
        await update.message.reply_text(
            render_template("start.jinja") + always_display_text, reply_markup=kb
        )
    context.user_data.clear()
    return StartHandlerState.SELECTING_ACTION


async def get_current_keyboard(update: Update):
    user_tg_id = update.effective_user.id
    try:
        user = await get_user_by_tg_id(user_tg_id)
        status = user.status
    except UserError as e:
        logging.getLogger(__name__).exception(e)
        if is_admin(user_tg_id):
            kb = KB_START_COMMAND_ADMIN
        else:
            kb = KB_START_COMMAND
    else:
        # if is_admin(user_tg_id) and status == LECTURER_STATUS:
        #     kb = KB_START_COMMAND_REGISTERED_LECTURER_ADMIN
        if is_admin(user_tg_id):
            kb = KB_START_COMMAND_REGISTERED_ADMIN
        # elif status == LECTURER_STATUS:
        #     kb = KB_START_COMMAND_REGISTERED_LECTURER
        # else:
        #     kb = KB_START_COMMAND_REGISTERED
    # if is_admin(user_tg_id):
    #     kb = KB_START_COMMAND_ADMIN
    # else:
    #     kb = KB_START_COMMAND
    return kb


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_user.send_message("Операция приостановлена!")
    context.user_data["START_OVER"] = True
    await start_command(update, context)
    return END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    await update.message.reply_text("Все завершено!")

    return END

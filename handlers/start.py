import logging
from telegram import Update
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
from services.states import StartHandlerState
from services.templates import render_template


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    kb = await get_current_keyboard(update)

    await update.message.reply_text(render_template("start.jinja"), reply_markup=kb)
    return StartHandlerState.START


async def get_current_keyboard(update: Update):
    user_tg_id = update.effective_user.id
    try:
        user = await get_user_by_tg_id(user_tg_id)
        status = user.status
    except UserError as e:
        logging.getLogger(__name__).exception(e)
        if ADMIN_FILTER.check_update(update):
            kb = KB_START_COMMAND_ADMIN
        else:
            kb = KB_START_COMMAND
    else:
        if (
            ADMIN_FILTER.check_update(update) or is_admin(user_tg_id)
        ) and status == LECTURER_STATUS:
            kb = KB_START_COMMAND_REGISTERED_LECTURER_ADMIN
        elif ADMIN_FILTER.check_update(update) or is_admin(user_tg_id):
            kb = KB_START_COMMAND_REGISTERED_ADMIN
        elif status == LECTURER_STATUS:
            kb = KB_START_COMMAND_REGISTERED_LECTURER
        else:
            kb = KB_START_COMMAND_REGISTERED

    return kb

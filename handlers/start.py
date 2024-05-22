import logging
from telegram import Update
from telegram.ext import ContextTypes

from services.db import get_user
from services.exceptions import UserError
from services.filters import ADMIN_FILTER, LECTURER_FILTER
from services.kb import (
    KB_START_COMMAND,
    KB_START_COMMAND_ADMIN,
    KB_START_COMMAND_REGISTERED,
    KB_START_COMMAND_REGISTERED_ADMIN,
    KB_START_COMMAND_REGISTERED_LECTURER,
    KB_START_COMMAND_REGISTERED_LECTURER_ADMIN,
)
from services.states import StartHandlerStates
from services.templates import render_template


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tg_id = update.message.from_user.id
    try:
        user = await get_user(user_tg_id)
    except UserError as e:
        logging.getLogger(__name__).exception(e)
        if not ADMIN_FILTER.check_update(update):
            kb = KB_START_COMMAND_ADMIN
        else:
            kb = KB_START_COMMAND
    else:
        if ADMIN_FILTER.check_update(update) and LECTURER_FILTER.check_update(update):
            kb = KB_START_COMMAND_REGISTERED_LECTURER_ADMIN
        elif ADMIN_FILTER.check_update(update):
            kb = KB_START_COMMAND_REGISTERED_ADMIN
        elif LECTURER_FILTER.check_update(update):
            kb = KB_START_COMMAND_REGISTERED_LECTURER
        else:
            kb = KB_START_COMMAND_REGISTERED

    await update.message.reply_text(render_template("start.jinja"), reply_markup=kb)
    return StartHandlerStates.START

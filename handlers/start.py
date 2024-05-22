import logging
from telegram import Update
from telegram.ext import ContextTypes, filters

from services.db import get_user
from services.exceptions import UserError
from services.filters import ADMIN_FILTER, LECTURER_FILTER, is_admin, is_lecturer
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


async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    kb = await get_current_keyboard(update)

    await update.message.reply_text(render_template("start.jinja"), reply_markup=kb)
    return StartHandlerStates.START


async def get_current_keyboard(update: Update):
    user_tg_id = update.effective_user.id
    try:
        await get_user(user_tg_id)
    except UserError as e:
        logging.getLogger(__name__).exception(e)
        if ADMIN_FILTER.check_update(update):
            kb = KB_START_COMMAND_ADMIN
        else:
            kb = KB_START_COMMAND
    else:
        logging.getLogger(__name__).info(f"{ADMIN_FILTER.check_update(update)=}")
        if (ADMIN_FILTER.check_update(update) or is_admin(user_tg_id)) and (
            LECTURER_FILTER.check_update(update) or is_lecturer(user_tg_id)
        ):
            kb = KB_START_COMMAND_REGISTERED_LECTURER_ADMIN
        elif ADMIN_FILTER.check_update(update) or is_admin(user_tg_id):
            kb = KB_START_COMMAND_REGISTERED_ADMIN
        elif LECTURER_FILTER.check_update(update) or is_lecturer(user_tg_id):
            kb = KB_START_COMMAND_REGISTERED_LECTURER
        else:
            kb = KB_START_COMMAND_REGISTERED

    return kb

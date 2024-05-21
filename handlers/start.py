from telegram import Update
from telegram.ext import ContextTypes

from services.db import get_user
from services.kb import KB_START_COMMAND, KB_START_COMMAND_REGISTERED
from services.states import StartHandlerStates
from services.templates import render_template


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.message.from_user.id)
    if user is None:
        kb = KB_START_COMMAND

    kb = KB_START_COMMAND_REGISTERED
    await update.message.reply_text(render_template("start.jinja"), reply_markup=kb)
    return StartHandlerStates.START

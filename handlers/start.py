import logging
from telegram import Update, User
from telegram.ext import ContextTypes

from services.db import get_user
from services.exceptions import UserError
from services.kb import KB_START_COMMAND, KB_START_COMMAND_REGISTERED
from services.templates import render_template

START, ACTIVATE_KEY = range(2)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user(update.message.from_user.id)
    if user is None:
        kb = KB_START_COMMAND
    kb = KB_START_COMMAND_REGISTERED
    await update.message.reply_text(render_template("start.jinja"), reply_markup=kb)
    return START

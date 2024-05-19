from telegram import Update
from telegram.ext import ContextTypes

from services.kb import KB_START_COMMAND
from services.templates import render_template

START, ACTIVATE_KEY = range(2)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        render_template("start.jinja"), reply_markup=KB_START_COMMAND
    )
    return START

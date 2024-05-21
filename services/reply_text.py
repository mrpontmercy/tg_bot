from telegram import Update
from telegram.constants import ParseMode

from services.templates import render_template


async def send_error_message(
    update: Update, data: dict | None = None, err: str | None = None
):
    await update.message.reply_text(
        render_template("error.jinja", err=err), parse_mode=ParseMode.HTML
    )

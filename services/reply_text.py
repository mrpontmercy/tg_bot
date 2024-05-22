from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services.templates import render_template


async def send_error_message(
    user_tg_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    data: dict | None = None,
    err: str | None = None,
):
    await context.bot.send_message(
        user_tg_id,
        render_template("error.jinja", err=err, data=data),
        parse_mode=ParseMode.HTML,
    )

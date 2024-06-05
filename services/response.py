from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services.templates import render_template


async def send_message(
    tg_id: int,
    template_name: str,
    context: ContextTypes.DEFAULT_TYPE,
    kb: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    data: dict | None = None,
    replace: bool = True,
):
    await context.bot.send_message(
        tg_id,
        render_template(template_name, data=data, replace=replace),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )

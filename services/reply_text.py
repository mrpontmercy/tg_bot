from telegram import Update
from telegram.constants import ParseMode

from services.templates import render_template


async def reply_text(
    update: Update, template_name: str, data: dict | None = None, err: str | None = None
):
    await update.message.reply_text(
        render_template(template_name, err=err, **data), parse_mode=ParseMode.HTML
    )

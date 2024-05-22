import logging

from telegram.ext import ContextTypes
from services.db import get_user
from services.exceptions import UserError


async def notify_lecturer(lecturer_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = await get_user(lecturer_id)
    except UserError as e:
        logging.getLogger(__name__).exception(e)
        return None

    # Написать на какое занятие записались
    await context.bot.send_message(user.telegram_id, "На занятие записались")

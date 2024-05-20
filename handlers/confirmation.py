# Написать функцию обработчик для подтверждения записи на урок/отмены записи на урок

from telegram import Update
from telegram.ext import ContextTypes

from services.kb import KB_CONFIRMATION


async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.edit_text(
        "Вы действительно хотите выполнить это действие?", reply_markup=KB_CONFIRMATION
    )

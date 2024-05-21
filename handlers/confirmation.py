# Написать функцию обработчик для подтверждения записи на урок/отмены записи на урок

import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes

from handlers.admin import remove_subscription
from handlers.lesson import cancel_lesson, subscribe_to_lesson
from services.kb import KB_CONFIRMATION, get_confirmation_keyboard


async def confirmation_action_handler(update: Update, _: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prefix = query.data.split("_")[-1]
    confirm_kb = get_confirmation_keyboard(prefix)
    await query.edit_message_text(
        "Вы действительно хотите выполнить это действие?", reply_markup=confirm_kb
    )


async def confirm_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    logging.getLogger(__name__).info(f"{query.data=}")
    action = query.data.split("_")[0]
    match action:
        case "subscribe":
            await subscribe_to_lesson(update, context)
        case "cancel":
            await cancel_lesson(update, context)
        case "deleteSub":
            try:
                await remove_subscription(update, context)
                await query.edit_message_text("Абонемент успешно удален!")
            except sqlite3.Error as e:
                logging.getLogger(__name__).exception(e)
                return await query.edit_message_text("Не удалось удалить абонемент!")


async def cancel_action_button(update: Update, _: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Действие отменено", reply_markup=None)

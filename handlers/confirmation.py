# Написать функцию обработчик для подтверждения записи на урок/отмены записи на урок

import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes

from config import (
    CALLBACK_DATA_CANCEL_LESSON,
    CALLBACK_DATA_CANCEL_LESSON_LECTURER,
    CALLBACK_DATA_DELETESUBSCRIPTION,
    CALLBACK_DATA_SUBSCRIBE,
)
from handlers.admin.admin import list_available_subs, remove_subscription
from handlers.lecturer.lecturer import cancel_lesson_by_lecturer, show_lecturer_lessons
from handlers.student.lesson import (
    cancel_lesson,
    show_lessons,
    show_my_lessons,
    subscribe_to_lesson,
)
from services.kb import get_confirmation_keyboard


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

    # action_confirm_action
    action = query.data.split("_")[0]
    if action == CALLBACK_DATA_SUBSCRIBE:
        await subscribe_to_lesson(update, context)
        # await show_lessons(update, context)
    elif action == CALLBACK_DATA_CANCEL_LESSON:
        await cancel_lesson(update, context)
        # await show_my_lessons(update, context)
    elif action == CALLBACK_DATA_CANCEL_LESSON_LECTURER:
        await cancel_lesson_by_lecturer(update, context)
        await show_lecturer_lessons(update, context)
    elif action == CALLBACK_DATA_DELETESUBSCRIPTION:
        try:
            return await remove_subscription(update, context)
            # await list_available_subs(update, context)
        except sqlite3.Error as e:
            logging.getLogger(__name__).exception(e)
            return await query.edit_message_text("Не удалось удалить абонемент!")


async def cancel_action_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split("_")[0]
    if action == CALLBACK_DATA_SUBSCRIBE:
        await show_lessons(update, context)
    elif action == CALLBACK_DATA_CANCEL_LESSON:
        await show_my_lessons(update, context)
    elif action == CALLBACK_DATA_DELETESUBSCRIPTION:
        await list_available_subs(update, context)

    # await query.edit_message_text("Действие отменено")

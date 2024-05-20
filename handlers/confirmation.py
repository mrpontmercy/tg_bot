# Написать функцию обработчик для подтверждения записи на урок/отмены записи на урок

from telegram import Update
from telegram.ext import ContextTypes

from services.kb import KB_CONFIRMATION
from services.states import ConfirmStates, StartHandlerStates


async def confirm_your_action(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.edit_text(
        "Вы действительно хотите выполнить это действие?", reply_markup=KB_CONFIRMATION
    )
    return ConfirmStates.CONFIRMATION


async def cancel_action_button(update: Update, _: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Действие отменено!")

    return ConfirmStates.CANCEL

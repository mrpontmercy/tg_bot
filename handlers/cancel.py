from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Операция отменена", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

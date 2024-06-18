from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.callback_query.answer()
    await update.effective_message.reply_text("Операция отменена")
    return ConversationHandler.END


async def sub_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text("Операция отменена")
    return ConversationHandler.END

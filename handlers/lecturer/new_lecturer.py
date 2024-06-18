from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler

from handlers.lecturer.lecturer import edit_title_lesson
from services.kb import get_keyboard_edit_lesson
from services.states import EditLessonState


async def start_editing_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback_query = update.callback_query
    await callback_query.answer()
    message = update.effective_message.text_html
    message += "\n\n <b>Выберите что хотите изменить у текущего урока?</b>"
    kb = get_keyboard_edit_lesson()
    await callback_query.edit_message_text(
        message, reply_markup=kb, parse_mode=ParseMode.HTML
    )

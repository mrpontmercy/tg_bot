import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from config import BASE_DIR, LESSONS_DIR, CALLBACK_LESSON_PATTERN
from db import execute, fetch_all
from handlers.kb import get_keyboard
from services.cources import get_lessons_from_db, get_lessons_from_file

SEND_FILE = 1


async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id
    await context.bot.send_message(
        chat_id,
        "Отправьте файл с уроками установленной формы.\n"
        "Чтобы завершить операцию нажмите: /cancel",
    )
    return SEND_FILE


async def insert_into_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rec_file = update.message.document
    file = await context.bot.get_file(rec_file)
    saved_file_path = LESSONS_DIR / rec_file.file_name
    await file.download_to_drive(saved_file_path)
    lessons = get_lessons_from_file(saved_file_path)
    for lesson in lessons:
        params = lesson.to_dict()
        await execute(
            """INSERT INTO course (title, time_start, lecturer) VALUES (:title, :time_start, :lecturer)""",
            params,
        )
    os.remove(saved_file_path)
    await context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text="Уроки успешно добавлены в общий список",
    )
    return ConversationHandler.END


async def canlec_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Операция прервана")
    return ConversationHandler.END


async def show_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lessons = await get_lessons_from_db()
    context.user_data["lessons"] = lessons
    answer = "\n".join(lessons[0].values())
    kb = get_keyboard(0, len(lessons), CALLBACK_LESSON_PATTERN)
    await context.bot.send_message(
        update.effective_chat.id,
        text=answer,
        reply_markup=kb,
    )


async def lessons_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lessons = context.user_data["lessons"]
    current_index = int(query.data[len(CALLBACK_LESSON_PATTERN) :])
    answer = "\n".join(lessons[current_index].values())
    await query.edit_message_text(
        answer,
        reply_markup=get_keyboard(current_index, len(lessons), CALLBACK_LESSON_PATTERN),
    )

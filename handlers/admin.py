import os
import random
import string

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import CALLBACK_SUB_PATTERN, LESSONS_DIR
from db import execute
from services.kb import get_flip_with_cancel_INLINEKB
from services.lesson import get_lessons_from_file
from services.subscription import get_available_subs, get_subs
from services.templates import render_template


unity = string.ascii_letters + string.digits

CHOOSING, GET_CSV_FILE, NUM_OF_CLASSES = range(3)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup(
        [["Создать ключ", "Доступные ключи", "Обновить уроки"]], one_time_keyboard=True
    )
    await update.message.reply_text(
        "Привет, в режиме АДМИНА можно создать ключ подписки. Нажми соответствующую кнопку!\n\nЧтобы прервать эту коману напиши: cancel или /cancel",
        reply_markup=kb,
    )
    return CHOOSING


async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id
    await context.bot.send_message(
        chat_id,
        "Отправьте файл с уроками установленной формы.\n"
        "Чтобы завершить операцию нажмите: /cancel",
        reply_markup=ReplyKeyboardRemove(),
    )
    return GET_CSV_FILE


async def insert_into_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rec_file = update.message.document
    file = await context.bot.get_file(rec_file)
    saved_file_path = LESSONS_DIR / rec_file.file_name
    await file.download_to_drive(saved_file_path)
    lessons = get_lessons_from_file(saved_file_path)
    if lessons is None:
        await update.effective_user.send_message(
            "Неверно заполнен файл. Попробуй с другим файлом."
        )
        return GET_CSV_FILE
    for lesson in lessons:
        params = lesson.to_dict()
        # TODO добавить tg_id_lecturer
        await execute(
            """INSERT INTO lesson (title, time_start, num_of_seats, lecturer, tg_id_lecturer) VALUES (:title, :time_start,:num_of_seats, :lecturer, :tg_id_lecturer)""",
            params,
        )
    os.remove(saved_file_path)
    await context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text="Уроки успешно добавлены в общий список",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def list_available_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.effective_message.reply_text(
        "Предыдущая клавиатура удалена", reply_markup=ReplyKeyboardRemove()
    )
    subs = await get_available_subs()
    context.user_data["subs"] = subs
    kb = get_flip_with_cancel_INLINEKB(0, len(subs), CALLBACK_SUB_PATTERN)
    sub = list(subs[0].values())
    await message.reply_text(
        text=render_template(
            "subs.jinja",
            {"sub_key": sub[0], "num_of_classes": sub[1]},
        ),
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def subs_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    subs = await get_available_subs()
    current_index = int(query.data[len(CALLBACK_SUB_PATTERN) :])
    sub = list(subs[current_index].values())
    await query.edit_message_text(
        text=render_template(
            "subs.jinja",
            {
                "sub_key": sub[0],
                "num_of_classes": sub[1],
            },
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=get_flip_with_cancel_INLINEKB(
            current_index, len(subs), CALLBACK_SUB_PATTERN
        ),
    )


async def generate_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = await get_subs()
    while True:
        sub_key = "".join(random.choices(unity, k=20))
        if not any([True if sub_key in el else False for el in subs]):
            break

    context.user_data["sub_key"] = sub_key
    answer = f"Отлично, теперь введите количество уроков для подписки!"
    await update.effective_user.send_message(answer, reply_markup=ReplyKeyboardRemove())
    return NUM_OF_CLASSES


async def send_num_of_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    num_of_classes = update.message.text  # TODO validate text
    sub_key = context.user_data["sub_key"]
    await execute(
        """insert into subscription (sub_key, num_of_classes) VALUES (:sub_key, :num_of_classes)""",
        {
            "sub_key": sub_key,
            "num_of_classes": num_of_classes,
        },
    )
    answer = (
        f"Подписка успешно создана:\n\nПолученный код нужно передать пользователю."
        f"Он должен активировать его через команду /activate_key\n\n"
        f"Код:\t{sub_key}\n\n"
    )
    await update.effective_message.reply_text(answer)
    context.user_data.clear()
    return ConversationHandler.END

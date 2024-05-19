import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from all_strings import GREETINGS
from db import execute, fetch_one
from services.register import (
    insert_user,
    validate_message,
)

REGISTER = 1

logger = logging.getLogger(__name__)


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, GREETINGS)
    return REGISTER


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    full_info = [user.id, user.username] + update.effective_message.text.split(" ")
    try:
        validated_message = validate_message(full_info)
    except BaseException as e:
        return await update.effective_message.reply_text(
            "Ошибка в данных, попробуйте снова. Возможная ошибка \n\n" + e
        )

    params = validated_message.to_dict()
    try:
        await insert_user(params)
    except sqlite3.Error as e:
        logger.exception(e)
        await context.bot.send_message(
            user.id,
            "Произошла ошибка.\nНачните регистрацию заново: /register",
        )
        return ConversationHandler.END

    await context.bot.send_message(user.id, "Вы успешно зарегестрировались!")

    return ConversationHandler.END


async def activate_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.effective_message.reply_text(
            "Необходимо ввести код после команды.\nПопробуйте снова."
        )
        return

    sub_user_id = await fetch_one(
        "select u.id from user u join subscription s on u.id=s.user_id"
    )
    sub_user_id = sub_user_id["id"]
    sub_key = context.args[0]
    res_d = await fetch_one(
        "SELECT sub_key, num_of_classes, user_id from subscription where sub_key=:sub_key",
        {"sub_key": sub_key},
    )
    if res_d is None:
        return await update.effective_message.reply_text(
            "Данный ключ невалиден. Обратитесь за другим ключом."
        )
    elif res_d["user_id"] is not None:
        return await update.effective_message.reply_text(
            "Данный ключ уже зарегестрирован.\nОбратитесь за другим ключом."
        )
    if sub_user_id:
        num_of_classes_left = await fetch_one(
            "select num_of_classes from subscription where user_id=:user_id",
            {"user_id": sub_user_id},
        )
        num_of_classes_left = num_of_classes_left["num_of_classes"]
        result_num_of_classes = num_of_classes_left + res_d["num_of_classes"]
        await execute(
            "delete from subscription where user_id=:user_id", {"user_id": sub_user_id}
        )
        await execute(
            "update subscription set user_id=:user_id, num_of_classes=:num_of_classes WHERE sub_key=:sub_key",
            {
                "num_of_classes": result_num_of_classes,
                "user_id": sub_user_id,
                "sub_key": sub_key,
            },
        )
        return await update.effective_message.reply_text("Подписка успешно обновлена!")
    sql = """update subscription set user_id=u.id FROM (select id from users where telegram_id=:tg_id) u WHERE sub_key=:sub_key"""
    # TODO сделать обновление абонимента, если вводится новый валидный ключ
    # (нужно сохранять оставшееся количество дней и плюсовать с новой подпиской)
    await execute(sql, {"tg_id": update.effective_user.id, "sub_key": sub_key})
    await update.message.reply_text("Ваша подписка успешно оформлена")

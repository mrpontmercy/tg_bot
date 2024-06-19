import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from handlers.start import get_current_keyboard
from services.kb import get_back_kb, get_retry_or_back_keyboard
from services.response import edit_callbackquery
from services.subscription import activate_key, validate_args
from services.exceptions import (
    InputMessageError,
    InvalidSubKey,
    SubscriptionError,
    UserError,
)
from services.db import get_user_by_tg_id
from services.lesson import get_user_subscription
from services.reply_text import send_error_message, send_error_query_message
from services.states import END, StartHandlerState
from services.utils import (
    add_message_info_into_context,
    add_start_over,
    delete_message_from_context,
)

logger = logging.getLogger(__name__)


@add_message_info_into_context
@add_start_over
async def start_activating_subkey(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()
    kb = get_back_kb(END)
    try:
        user = await get_user_by_tg_id(update.effective_user.id)
    except UserError as e:
        await edit_callbackquery(query=query, err=str(e), keyboard=kb)
        return StartHandlerState.SHOWING

    await query.edit_message_text("Отправьте ключ абонимента!")
    context.user_data["curr_user_tg_id"] = user.telegram_id
    return StartHandlerState.ACTIVATE_KEY


async def register_sub_key_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mess_args = update.message.text.split(" ")
    user_tg_id = context.user_data.get("curr_user_tg_id")
    kb = get_retry_or_back_keyboard(StartHandlerState.START_ACTIVATE_KEY, END)
    await delete_message_from_context(context)
    try:
        args = validate_args(mess_args)
    except InputMessageError as e:
        await send_error_message(user_tg_id, context, err=str(e), keyboard=kb)
        return StartHandlerState.SHOWING

    sub_key = args[0]
    if user_tg_id is None:
        await send_error_message(user_tg_id, context, err=str(e), keyboard=kb)
        return StartHandlerState.SHOWING

    del context.user_data["curr_user_tg_id"]
    try:
        user = await get_user_by_tg_id(user_tg_id)
        final_message = await activate_key(sub_key, user)
    except (InvalidSubKey, UserError) as e:
        logger.exception(e)
        await send_error_message(user_tg_id, context, err=str(e), keyboard=kb)
        return StartHandlerState.SHOWING
    except sqlite3.Error as e:
        logger.exception(e)
        await send_error_message(
            user_tg_id,
            context,
            err="Не удалось выполнить операцию.",
            keyboard=kb,
        )
        return StartHandlerState.SHOWING

    curr_kb = await get_current_keyboard(update)
    await update.effective_message.reply_text(final_message, reply_markup=curr_kb)

    return StartHandlerState.SELECTING_ACTION


@add_start_over
@add_message_info_into_context
async def show_number_of_remaining_classes_on_subscription(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    kb = get_back_kb(END)
    await query.answer()
    tg_id = update.effective_user.id
    user = await get_user_by_tg_id(tg_id)
    try:
        subscription = await get_user_subscription(user_db_id=user.id)
    except SubscriptionError as e:
        await edit_callbackquery(query, "error.jinja", err=str(e), keyboard=kb)
        return StartHandlerState.SHOWING

    await query.edit_message_text(
        f"У вас осталось {subscription.num_of_classes} занятий на абонименте",
        reply_markup=kb,
    )
    return StartHandlerState.SHOWING

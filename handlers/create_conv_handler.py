from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler

from handlers.admin.admin import admin_command
from handlers.start import start_command
from handlers.student.lesson import show_lessons
from services.states import END, FlipKBState, StartHandlerState


def create_hanlder(
    callback_entry, callback_arrows, entry_pattern, pattern_prefix, end_state, fallback
):
    ch = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback_entry, pattern=f"^{entry_pattern}$")
        ],
        states={
            FlipKBState.START: [
                CallbackQueryHandler(
                    callback_arrows, pattern="^" + pattern_prefix + "\d+"
                )
            ],
        },
        fallbacks=[CallbackQueryHandler(fallback, pattern=f"^{END}$")],
        map_to_parent={END: end_state},
    )
    return ch


async def return_back_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["START_OVER"] = True
    await start_command(update, context)
    return END


async def return_back_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await admin_command(update, context)
    return END

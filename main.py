import logging
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import config
from db import close_db
from handlers.courses import (
    SEND_FILE,
    insert_into_course,
    lessons_button,
    show_lessons,
    update_command,
)
from handlers.register import (
    REGISTER,
    canlec_registration,
    register_command,
    register_user,
)

# from services.cources import update_course_table

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

if config.TELEGRAM_BOT_TOKEN is None:
    raise ValueError(f"Не указан Telegram Token!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.effective_user.id
    )


async def update_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update.effective_message.document.file_name)


def main():

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        [CommandHandler(["register"], register_command)],
        states={REGISTER: [MessageHandler(filters.TEXT, register_user)]},
        fallbacks=[
            CommandHandler(["cancel"], canlec_registration),
            MessageHandler(filters.Regex("cancel"), canlec_registration),
        ],
    )
    conv_handler2 = ConversationHandler(
        [CommandHandler(["update"], update_command)],
        states={
            SEND_FILE: [
                MessageHandler(
                    filters.Document.MimeType("text/csv"), insert_into_course
                )
            ]
        },
        fallbacks=[
            CommandHandler(["cancel"], canlec_registration),
            MessageHandler(filters.Regex("cancel"), canlec_registration),
        ],
    )
    app.add_handler(conv_handler)
    app.add_handler(conv_handler2)
    app.add_handler(CommandHandler(["show_lessons"], show_lessons))
    app.add_handler(CallbackQueryHandler(lessons_button))

    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        logger.warning(traceback.format_exc())
    finally:
        close_db()

import logging
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
)
import config
from db import close_db
from init_handlers import (
    ADMIN_HANDLER,
    CQH_CANCEL_LESSON,
    CQH_LESSON_BUTTONS,
    CQH_SUBSCRIBE_LESSON,
    CQH_USER_LESSON_BUTTONS,
    REGISTER_USER_HANDLER,
    START_HANDLER,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

if config.TELEGRAM_BOT_TOKEN is None:
    raise ValueError(f"Не указан Telegram Token!")


def main():

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(ADMIN_HANDLER)
    app.add_handler(START_HANDLER)
    app.add_handler(REGISTER_USER_HANDLER)
    app.add_handler(CQH_SUBSCRIBE_LESSON)
    app.add_handler(CQH_CANCEL_LESSON)
    app.add_handler(CQH_LESSON_BUTTONS)
    app.add_handler(CQH_USER_LESSON_BUTTONS)

    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        logger.warning(traceback.format_exc())
    finally:
        close_db()

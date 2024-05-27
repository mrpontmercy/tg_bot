import logging
from telegram.ext import (
    Application,
)
import config
from db import close_db
from init_handlers import (
    ADMIN_HANDLER,
    CQH_AVAILABLE_SUBS_BUTTONS,
    CQH_CONFIRM_SUBCRIBE_CANCEL,
    CQH_CONFIRM_SUBCRIBE_YES,
    CQH_CONFIRM_SUBSCRIBE,
    CQH_LECTURER_START_EDIT_LESSON_BUTTONS,
    CQH_LECTURER_LESSON_BUTTONS,
    CQH_LESSON_BUTTONS,
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
    app.add_handler(CQH_AVAILABLE_SUBS_BUTTONS)
    app.add_handler(START_HANDLER)
    app.add_handler(REGISTER_USER_HANDLER)
    app.add_handler(CQH_CONFIRM_SUBSCRIBE)
    app.add_handler(CQH_CONFIRM_SUBCRIBE_YES)
    app.add_handler(CQH_CONFIRM_SUBCRIBE_CANCEL)
    app.add_handler(CQH_LESSON_BUTTONS)
    app.add_handler(CQH_USER_LESSON_BUTTONS)
    app.add_handler(CQH_LECTURER_LESSON_BUTTONS)
    app.add_handler(CQH_LECTURER_START_EDIT_LESSON_BUTTONS)

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        logger.warning(traceback.format_exc())
    finally:
        close_db()

import os
from pathlib import Path
import dotenv

dotenv.load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

SQLITE_DB_FILE = BASE_DIR / "db.sqlite3"
LESSONS_DIR = BASE_DIR / "course_files"
TEMPLATE_DIR = BASE_DIR / "templates"

CALLBACK_LESSON_PREFIX = "lesson_"
CALLBACK_USER_LESSON_PREFIX = "user_lesson_"
CALLBACK_SUB_PREFIX = "sub_"

CALLBACK_DATA_SUBSCRIBE = "subscribe"
CALLBACK_DATA_CANCEL_LESSON = "cancelLesson"
CALLBACK_DATA_DELETESUBSCRIPTION = "deleteSub"

DATETIME_FORMAT = "%Y-%m-%d %H:%M"

import os
from pathlib import Path
import dotenv

dotenv.load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

SQLITE_DB_FILE = BASE_DIR / "db.sqlite3"
LESSONS_DIR = BASE_DIR / "course_files"

CALLBACK_LESSON_PATTERN = "lesson_"

import csv
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes
from aiosqlite import Error

from config import DATETIME_FORMAT
from db import fetch_all, fetch_one, get_db
from services.db import (
    execute_delete,
    execute_insert,
    execute_update,
    fetch_one_subscription_where_cond,
    get_user_by_tg_id,
    select_where,
)
from services.exceptions import (
    ColumnCSVError,
    LessonError,
    SubscriptionError,
    UserError,
)
from services.utils import Lesson, Subscription, TransientLesson, UserID


async def update_info_after_cancel_lesson(lesson: Lesson, user: UserID):
    try:
        curr_sub = await get_user_subscription(user.id)
    except SubscriptionError as e:
        raise
    try:
        await execute_update(
            "lesson",
            "num_of_seats=:num_of_seats",
            "id=:l_id",
            {"num_of_seats": lesson.num_of_seats + 1, "l_id": lesson.id},
            autocommit=False,
        )

        await execute_update(
            "subscription",
            "num_of_classes=:num_of_classes",
            "user_id=:user_id",
            {"num_of_classes": curr_sub.num_of_classes + 1, "user_id": user.id},
            autocommit=False,
        )

        await execute_delete(
            "user_lesson",
            "lesson_id=:lesson_id AND user_id=:user_id",
            {"user_id": user.id, "lesson_id": lesson.id},
            autocommit=False,
        )
    except Error as e:
        await (await get_db()).rollback()
        raise

    await (await get_db()).commit()


async def get_user_subscription(user_db_id: int):
    subsciption_by_user = await fetch_one_subscription_where_cond(
        "user_id=:user_id",
        {"user_id": user_db_id},
    )
    if subsciption_by_user is None:
        raise SubscriptionError("У пользователя нет абонимента")
    elif subsciption_by_user.num_of_classes == 0:
        raise SubscriptionError(
            "В вашем абонименте не осталось занятий. Обратитесь за новым абониментом!"
        )

    return subsciption_by_user


async def already_subscribed_to_lesson(lesson_id, user_id):
    sql = select_where("user_lesson", "id", "user_id=:user_id AND lesson_id=:lesson_id")
    is_subscribed = await fetch_one(sql, {"user_id": user_id, "lesson_id": lesson_id})
    if is_subscribed is None:
        return False
    return True


async def process_sub_to_lesson(lesson: Lesson, sub: Subscription):
    is_subscribed = await already_subscribed_to_lesson(lesson.id, sub.user_id)
    if is_subscribed:
        raise LessonError("Вы уже записались на это занятие!")
    try:
        await execute_update(
            "lesson",
            "num_of_seats=:seats_left",
            "id=:lesson_id",
            {
                "seats_left": lesson.num_of_seats - 1,
                "lesson_id": lesson.id,
            },
            autocommit=False,
        )
        await execute_update(
            "subscription",
            "num_of_classes=:num_class_left",
            "user_id=:user_id",
            {
                "num_class_left": sub.num_of_classes - 1,
                "user_id": sub.user_id,
            },
            autocommit=False,
        )
        await execute_insert(
            "user_lesson",
            "user_id, lesson_id",
            ":user_id, :lesson_id",
            {
                "user_id": sub.user_id,
                "lesson_id": lesson.id,
            },
            autocommit=False,
        )
    except Error as e:
        await (await get_db()).rollback()
        raise
    await (await get_db()).commit()


def get_lessons_from_file(
    file_path: Path,
    fieldnames: tuple[str] = ("title", "time_start", "num_of_seats", "lecturer_phone"),
) -> list[TransientLesson] | None:
    lessons: list[TransientLesson] = []
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, fieldnames)
        for row in reader:
            try:
                l = TransientLesson(**row)
            except (TypeError, KeyError, ColumnCSVError) as e:
                logging.getLogger(__name__).exception(e)
                return None
            except Exception as e:
                logging.getLogger(__name__).exception(e)
                return None
            else:
                lessons.append(l)

    return lessons


async def get_available_upcoming_lessons_from_db(user_id: int):
    sql = """select l.id, l.title, l.time_start, l.num_of_seats, u.f_name || ' ' || u.s_name as lecturer_full_name, l.lecturer_id from lesson l 
            left join user_lesson ul on ul.lesson_id=l.id AND ul.user_id=:user_id join user u on u.id=l.lecturer_id 
            WHERE ul.lesson_id is NULL AND strftime("%Y-%m-%d %H:%M", "now", "4 hours") < l.time_start"""

    # select l.id, l.title, l.time_start, l.num_of_seats, l.lecturer_id, u.f_name from lesson l join user_lesson ul on ul.lesson_id=l.id AND ul.user_id=1 left join user u on u.id=l.lecturer_id WHERE ul.lesson_
    #     id is not NULL;
    rows = await fetch_all(sql, params={"user_id": user_id})
    if not rows:
        raise LessonError("Не удалось найти занятия")
    lessons: list[Lesson] = []
    for row in rows:
        lessons.append(Lesson(**row))

    return lessons


async def get_lecturer_lessons(lecturer_id: int):
    "select l.id, l.title, l.time_start, l.num_of_seats, u.f_name || ' ' || u.s_name, l.lecturer_id FROM lesson l join user u on u.id=l.lecturer_id WHERE l.lecturer_id=:lecturer_id"
    sql = select_where("lesson", "*", "lecturer_id=:lecturer_id")
    rows = await fetch_all(sql, {"lecturer_id": lecturer_id})

    if not rows:
        raise LessonError("Вы не ведете ни одного занятия!")

    lessons = []

    for row in rows:
        lessons.append(Lesson(**row))

    return lessons


async def get_user_upcoming_lessons(user_id) -> list[Lesson]:
    lessons = await fetch_all_user_upcoming_lessons(user_id)

    if lessons is None or not lessons:
        raise LessonError("Не удалось найти занятия пользователя!")

    res = []

    for row in lessons:
        res.append(Lesson(**row))

    return res


async def fetch_all_user_upcoming_lessons(user_id: str | int):
    sql = """select l.id, l.title, l.time_start, l.num_of_seats, u.f_name || ' ' || u.s_name as lecturer_full_name, l.lecturer_id from lesson l
            join user_lesson ul on l.id=ul.lesson_id join user u on u.id=l.lecturer_id WHERE ul.user_id=:user_id AND strftime('%Y-%m-%d %H:%M', 'now', '4 hours') < l.time_start"""  # не * а конкретные поля
    return await fetch_all(sql, {"user_id": user_id})


def is_possible_dt(lesson_start_dt):
    lesson_dt_utc = datetime.strptime(lesson_start_dt, DATETIME_FORMAT) - timedelta(
        hours=4
    )
    user_dt_utc = datetime.now(timezone.utc)
    user_dt_utc = datetime(
        user_dt_utc.year,
        user_dt_utc.month,
        user_dt_utc.day,
        user_dt_utc.hour,
        user_dt_utc.minute,
    )
    res = lesson_dt_utc - user_dt_utc
    if res.total_seconds() // 3600 < 2:
        return False
    return True


async def get_lessons_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE, lessons_func, state
):
    user_tg_id = context.user_data.get("curr_user_tg_id")
    if user_tg_id is None:
        await update.callback_query.edit_message_text("Что-то пошло не так")
        return None, state

    try:
        user = await get_user_by_tg_id(user_tg_id)
        lessons = await lessons_func(user.id)
    except (LessonError, UserError) as e:
        logging.getLogger(__name__).exception(e)
        await update.callback_query.edit_message_text(str(e))
        return None, state

    return lessons, None

import csv
import logging
from pathlib import Path

from db import fetch_all, fetch_one
from services.db import (
    execute_insert,
    execute_update,
    fetch_one_subscription_where_cond,
    fetch_one_user,
    select_where,
)
from services.exceptions import (
    ColumnCSVError,
    LessonError,
    SubscriptionError,
)
from services.utils import Lesson, Subscription


async def check_user_in_db(telegram_id: int):
    curr_user_db = await fetch_one_user({"telegram_id": telegram_id})

    return curr_user_db


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


def get_lessons_from_file(file_name: Path) -> list[Lesson] | None:
    lessons: list[Lesson] = []
    with open(file_name, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        try:
            for row in reader:
                lessons.append(Lesson(**row))
        except KeyError as e:
            logging.getLogger(__name__).exception(e)
            return None
        except ColumnCSVError("Неверно заполнен файл с уроками") as e:
            logging.getLogger(__name__).exception(e)
            return None

    return lessons


async def get_available_lessons_from_db():
    sql = (
        select_where(
            "lesson",
            "*",
            "num_of_seats>0",
        )
        + " ORDER BY time_start ASC"
    )

    rows = await fetch_all(sql)
    if not rows:
        raise LessonError("Не удалось найти занятия!")
    lessons: list[Lesson] = []
    for row in rows:
        lessons.append(Lesson(**row))

    return lessons


async def get_user_lessons(user_id) -> list[Lesson]:
    lessons = await _fetch_all_user_lessons(user_id)

    if lessons is None:
        raise LessonError("Не удалось найти занятия пользователя!")

    res = []
    for row in lessons:
        res.append(Lesson(**row))
    return res


async def _fetch_all_user_lessons(user_id: str | int):
    sql = """select l.id, l.title, l.time_start, l.num_of_seats, l.lecturer, l.tg_id_lecturer from lesson l \
            join user_lesson ul on l.id=ul.lesson_id WHERE ul.user_id=:user_id"""  # не * а конкретные поля
    return await fetch_all(sql, {"user_id": user_id})

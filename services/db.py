from typing import Any, Iterable
from db import execute, fetch_all, fetch_one
from services.exceptions import LessonError, UserError
from services.utils import Lesson, Subscription, UserID


def update_where_sql(table: str, set_val: str, conditions: str):
    return f"""UPDATE {table} SET {set_val} WHERE {conditions}"""


def delete_where_sql(table: str, conditions: str):
    return f"""DELETE FROM {table} WHERE {conditions}"""


def insert_sql(table: str, columns: str, values: str):
    return f"""INSERT INTO {table} ({columns}) VALUES ({values})"""


def select_where(table: str, columns: str, conditions: str):
    return f"""SELECT {columns} FROM {table} WHERE {conditions}"""


async def execute_insert(
    table: str,
    columns: str,
    values: str,
    params: Iterable[Any] | None = None,
    *,
    autocommit: bool = True,
):
    sql = insert_sql(table, columns, values)
    await execute(sql, params, autocommit=autocommit)


async def execute_update(
    table: str,
    set_val: str,
    conditions: str,
    params: Iterable[Any] | None = None,
    *,
    autocommit: bool = True,
):
    sql = update_where_sql(table, set_val, conditions)
    await execute(sql, params, autocommit=autocommit)


async def execute_delete(
    table: str,
    conditions: str,
    params: Iterable[Any] | None = None,
    *,
    autocommit: bool = True,
):
    sql = delete_where_sql(table, conditions)
    await execute(sql, params, autocommit=autocommit)


async def fetch_one_user(conditions: str, params: Iterable[Any]):
    sql = select_where("user", "*", conditions)
    row = await fetch_one(sql, params)
    return UserID(**row) if row is not None else None


async def fetch_one_subscription_where_cond(
    conditions: str,
    params: Iterable[Any],
) -> Subscription | None:
    sql = select_where("subscription", "*", conditions)
    row = await fetch_one(sql, params)
    return Subscription(**row) if row is not None else None


async def get_user_by_tg_id(telegram_id: int):
    user = await fetch_one_user("telegram_id=:telegram_id", {"telegram_id": telegram_id})

    if user is None:
        raise UserError("Пользователь не зарегестрирован")

    return user


async def get_user_by_id(user_id: int):
    user = await fetch_one_user("id=:user_id", {"user_id": user_id})
    if user is None:
        raise UserError("Пользователь не зарегестрирован")
    return user


async def get_users_by_id(user_ids: list[int]):
    placeholders = ", ".join("?" * len(user_ids))
    sql = select_where("user", "*", f"id IN ({placeholders})")
    rows = await fetch_all(sql, user_ids)

    if not rows:
        return None
    return [UserID(**row) for row in rows]


async def get_lecturer_upcomming_lessons(lecturer_id: int):
    sql = """select l.id, l.title, l.time_start, l.num_of_seats, u.f_name || ' ' || u.s_name as lecturer_full_name, l.lecturer_id FROM lesson l
            join user u on u.id=l.lecturer_id WHERE l.lecturer_id=:lecturer_id AND strftime("%Y-%m-%d %H:%M", "now", "4 hours") < l.time_start ORDER BY l.time_start"""
    rows = await fetch_all(sql, {"lecturer_id": lecturer_id})

    if not rows:
        raise LessonError("Не удалось найти занятия!")

    return [Lesson(**row) for row in rows]


async def get_user_by_phone_number(phone_number):
    sql = select_where("user", "*", "phone_number=:phone_number")
    row = await fetch_one(sql, {"phone_number": phone_number})
    if row is None:
        raise UserError("Пользователь с таким номером не зарегестрирован")
    return UserID(**row)


async def insert_lesson_in_db(params):
    await execute(
        """INSERT INTO lesson (title, time_start, num_of_seats, lecturer_id) VALUES (:title, :time_start,:num_of_seats, :lecturer_id)""",
        params,
    )


async def insert_lessons_into_db(params: list[Iterable[Any]]):
    for param in params:
        await insert_lesson_in_db(
            param,
        )


async def get_all_users_of_lesson(params_lesson_id: dict):
    user_ids = await fetch_all(
        "SELECT user_id from user_lesson where lesson_id=:lesson_id", params_lesson_id
    )

    all_students_of_lesson = await get_users_by_id(
        [v for item in user_ids for v in item.values()]
    )

    return all_students_of_lesson

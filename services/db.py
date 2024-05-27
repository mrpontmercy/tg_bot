from typing import Any, Iterable
from config import LECTURER_STR
from db import execute, fetch_all, fetch_one
from services.exceptions import UserError
from services.utils import Lesson, Subscription, UserID


def update_where_sql(table: str, set_val: str, conditions: str):
    return f"""UPDATE {table} SET {set_val} WHERE {conditions}"""


def delete_where_sql(table: str, conditions: str):
    return f"""DELETE FROM {table} WHERE {conditions}"""


def insert_sql(table: str, columns: str, values: str):
    return f"""INSERT INTO {table} ({columns}) VALUES ({values})"""


def select_where(table: str, columns: str, conditions: str):
    return f"""SELECT {columns} FROM {table} WHERE {conditions}"""  # TODO изменить аргумент, сделать чтобы условия передавались строкой


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


async def get_user(telegram_id: int):
    user = await fetch_one_user(
        "telegram_id=:telegram_id", {"telegram_id": telegram_id}
    )

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
    sql = """select l.id, l.title, l.time_start, l.num_of_seats, u.f_name || ' ' || u.s_name as lecturer, l.lecturer_id FROM lesson l
            join user u on u.id=l.lecturer_id WHERE l.lecturer_id=:lecturer_id AND strftime("%Y-%m-%d %H:%M", "now", "4 hours") < l.time_start"""
    rows = await fetch_all(sql, {"lecturer_id": lecturer_id})

    if not rows:
        return None

    return [Lesson(**row) for row in rows]


async def get_user_by_phone_number(phone_number):
    sql = select_where("user", "*", "phone_number=:phone_number")
    row = await fetch_one(sql, {"phone_number": phone_number})
    if row is None:
        raise UserError("Пользователь с таким номером не зарегестрирован")
    return UserID(**row) if row is not None else None


async def get_lecturers():
    sql = select_where("user", "*", f"status={LECTURER_STR}")
    rows = await fetch_all(sql)

    if not rows:
        return None

    res = []
    for row in rows:
        res.append(UserID(**row))

    return res

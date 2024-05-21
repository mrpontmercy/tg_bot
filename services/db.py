from typing import Any, Iterable, Literal
from db import execute, fetch_one
from services.exceptions import SubscriptionError, UserError
from services.utils import Subscription, UserID

Math_Symbols_TYPE = Literal["=", "<", ">", "<=", ">=" "!=", "<>"]


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


async def fetch_one_user_by_tg_id(params: Iterable[Any]):
    sql = select_where("user", "*", "telegram_id=:telegram_id")
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
    user = await fetch_one_user_by_tg_id({"telegram_id": telegram_id})

    if user is None:
        raise UserError("Пользователь не зарегестрирован")

    return user


async def get_user_by_phone_number(phone_number):
    sql = select_where("user", "*", "phone_number=:phone_number")
    row = await fetch_one(sql, {"phone_number": phone_number})
    if row is None:
        raise UserError("Пользователь с таким номером не зарегестрирован")
    return UserID(**row) if row is not None else None
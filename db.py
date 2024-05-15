import asyncio
import logging
from typing import Any, Iterable
import config

import aiosqlite

logger = logging.getLogger(__name__)


def sql_insert(table, values):
    columns = ", ".join(values.keys())
    vals = [values.values()]
    placeholdes = ", ".join("?" * len(values.keys()))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholdes})"


async def get_db():
    if not getattr(get_db, "db", None):
        db = await aiosqlite.connect(config.SQLITE_DB_FILE)
        get_db.db = db

    return get_db.db


async def fetch_all(sql, params: Iterable[Any] | None = None) -> list[dict]:
    cursor = await _get_cursor(sql, params)
    rows = await cursor.fetchall()
    results = []
    for row_ in rows:
        results.append(_get_result_with_column_names(cursor, row_))
    await cursor.close()
    return results


async def fetch_one(sql, params: Iterable[Any] | None = None) -> dict | None:
    cursor = await _get_cursor(sql, params)
    row_ = await cursor.fetchone()
    if not row_:
        await cursor.close()
        return None
    row = _get_result_with_column_names(cursor, row_)
    await cursor.close()
    return row


async def execute(
    sql, params: Iterable[Any] | None = None, *, autocommit: bool = True
) -> None:
    db = await get_db()
    args = (sql, params)

    # try:
    await db.execute(*args)
    # except Exception as e:
    #     logger.exception(e)
    #     return

    if autocommit:
        await db.commit()


def close_db():
    asyncio.run(_async_close_db())
    delattr(get_db, "db")


async def _async_close_db() -> None:
    await (await get_db()).close()


async def _get_cursor(sql, params: Iterable[Any] | None) -> aiosqlite.Cursor:
    db = await get_db()
    args = (sql, params)
    cursor = await db.execute(*args)
    db.row_factory = aiosqlite.Row
    return cursor


def _get_result_with_column_names(cursor: aiosqlite.Cursor, row: aiosqlite.Row) -> dict:
    column_names = [d[0] for d in cursor.description]
    resulting_row = {}
    for index, column_name in enumerate(column_names):
        resulting_row[column_name] = row[index]
    return resulting_row

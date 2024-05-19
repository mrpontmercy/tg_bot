from typing import Any, Iterable
from db import fetch_all


async def get_subs():
    r_sql = """SELECT sub_key FROM subscription"""
    return await fetch_all(r_sql)


async def get_available_subs():
    r_sql = """SELECT sub_key, num_of_classes FROM subscription WHERE user_id IS NULL"""
    return await fetch_all(r_sql)

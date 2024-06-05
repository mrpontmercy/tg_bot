import asyncio
import logging
import os
from telegram import Update
from telegram.ext import filters

from services.db import fetch_one_user, get_lecturers, get_user_by_tg_id
from services.exceptions import UserError

ADMINS = os.getenv("ADMINS")
if ADMINS is None or ADMINS == "":
    admins = []
else:
    admins = list(map(int, os.getenv("ADMINS").split(" ")))

ADMIN_FILTER = filters.User(admins)
PRIVATE_CHAT_FILTER = filters.ChatType.PRIVATE
ADMIN_AND_PRIVATE_FILTER = ADMIN_FILTER & PRIVATE_CHAT_FILTER

ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER = ADMIN_AND_PRIVATE_FILTER & ~filters.COMMAND

LECTURER_FILTER = filters.User()


def is_admin(user_id: int) -> bool:
    return user_id in admins

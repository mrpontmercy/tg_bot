import asyncio
import logging
import os
from telegram import Update
from telegram.ext import filters

from services.db import get_lecturers, get_user
from services.exceptions import UserError

admins = list(map(int, os.getenv("ADMINS").split(" ")))

ADMIN_FILTER = filters.User(admins)
PRIVATE_CHAT_FILTER = filters.ChatType.PRIVATE
ADMIN_AND_PRIVATE_FILTER = ADMIN_FILTER & PRIVATE_CHAT_FILTER

ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER = ADMIN_AND_PRIVATE_FILTER & ~filters.COMMAND


def get_lecturers_ids():
    loop = asyncio.get_event_loop()
    lecturers = loop.run_until_complete(get_lecturers())
    if lecturers is None:
        return []

    return [lecturer.id for lecturer in lecturers]


lecturer_ids = get_lecturers_ids()

if lecturer_ids:
    LECTURER_FILTER = filters.User(lecturer_ids)

LECTURER_FILTER = filters.User(allow_empty=True)

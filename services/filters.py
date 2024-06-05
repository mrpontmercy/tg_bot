import os
from telegram.ext import filters


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

import os
from telegram.ext import filters

admins = list(map(int, os.getenv("ADMINS").split(" ")))

ADMIN_FILTER = filters.User(admins)
PRIVATE_CHAT_FILTER = filters.ChatType.PRIVATE

ADMIN_AND_PRIVATE_FILTER = ADMIN_FILTER & PRIVATE_CHAT_FILTER

ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER = ADMIN_AND_PRIVATE_FILTER & ~filters.COMMAND

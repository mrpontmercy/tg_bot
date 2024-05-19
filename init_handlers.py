from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
import config
from handlers.activate import activate_key_command, register_sub_key_to_user
from handlers.admin import (
    CHOOSING,
    GET_CSV_FILE,
    NUM_OF_CLASSES,
    admin_command,
    generate_sub,
    insert_into_lesson,
    list_available_subs,
    send_num_of_classes,
    update_command,
)
from handlers.cancel import cancel
from handlers.lesson import (
    available_lessons_button,
    show_lessons,
    show_my_lessons,
    subscribe_to_lesson,
    user_lessons_button,
)
from handlers.register import REGISTER, register_command, register_user
from handlers.start import ACTIVATE_KEY, START, start_command


private_chat_filter = filters.ChatType.PRIVATE

START_HANDLER = ConversationHandler(
    entry_points=[
        CommandHandler(["start"], start_command, filters=private_chat_filter),
    ],
    states={
        START: [
            MessageHandler(
                filters.Regex("^Доступные занятия$") & private_chat_filter, show_lessons
            ),
            MessageHandler(
                filters.Regex("^Мои занятия$") & private_chat_filter, show_my_lessons
            ),
            MessageHandler(
                filters.Regex("^Активировать ключ$") & private_chat_filter,
                activate_key_command,
            ),
        ],
        ACTIVATE_KEY: [
            MessageHandler(
                filters=private_chat_filter
                & filters.Regex("^(?!cancel$)(?!Отменить$).+"),
                callback=register_sub_key_to_user,
            )
        ],
    },
    fallbacks=[
        CommandHandler(["cancel"], cancel, filters=private_chat_filter),
        MessageHandler(
            filters.Regex("^(cancel|Отменить)$") & private_chat_filter, cancel
        ),
    ],
)

REGISTER_USER_HANDLER = ConversationHandler(
    [CommandHandler(["register"], register_command, filters=private_chat_filter)],
    states={
        REGISTER: [MessageHandler(filters.TEXT & private_chat_filter, register_user)]
    },
    fallbacks=[
        CommandHandler(["cancel"], cancel, filters=private_chat_filter),
        MessageHandler(filters.Regex("cancel") & private_chat_filter, cancel),
    ],
)

ADMIN_HANDLER = ConversationHandler(
    [CommandHandler("admin", admin_command, filters=private_chat_filter)],
    {
        CHOOSING: [
            MessageHandler(
                filters.Regex("^Создать ключ$") & private_chat_filter, generate_sub
            ),
            MessageHandler(
                filters.Regex("^Доступные ключи$") & private_chat_filter,
                list_available_subs,
            ),
            MessageHandler(
                filters.Regex("^Обновить уроки$") & private_chat_filter, update_command
            ),
        ],
        GET_CSV_FILE: [
            MessageHandler(
                filters.Document.MimeType("text/csv") & private_chat_filter,
                insert_into_lesson,
            ),
        ],
        NUM_OF_CLASSES: [
            MessageHandler(
                filters.Regex("\d+") & private_chat_filter, send_num_of_classes
            )
        ],
    },
    [
        CommandHandler(["cancel"], cancel, filters=private_chat_filter),
        MessageHandler(
            filters=filters.Regex("cancel") & private_chat_filter, callback=cancel
        ),
    ],
)

SHOW_LESSONS_HANDLER = CommandHandler(
    ["show_lessons"], show_lessons, filters=private_chat_filter
)
SHOW_USER_LESSONS_HANDLER = CommandHandler(
    ["show_my_lessons"], show_my_lessons, filters=private_chat_filter
)

ACTIVATE_KEY_HANDLER = CommandHandler(
    ["activate_key"], activate_key_command, has_args=True, filters=private_chat_filter
)

CQH_SUBSCRIBE_LESSON = CallbackQueryHandler(
    subscribe_to_lesson, pattern="^" + config.CALLBACK_LESSON_PATTERN + "_subscribe$"
)

CQH_LESSON_BUTTONS = CallbackQueryHandler(
    available_lessons_button, pattern="^" + config.CALLBACK_LESSON_PATTERN
)
CQH_USER_LESSON_BUTTONS = CallbackQueryHandler(
    user_lessons_button, pattern="^" + config.CALLBACK_USER_LESSON_PATTERN
)

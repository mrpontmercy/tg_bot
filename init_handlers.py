from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
import config
from handlers.activate import (
    activate_key_command,
    register_sub_key_to_user,
    show_number_of_remaining_classes_on_subscription,
)
from handlers.admin import (
    CHOOSING,
    GET_CSV_FILE,
    LECTURER_PHONE,
    NUM_OF_CLASSES,
    admin_command,
    enter_lecturer_phone_number,
    generate_sub,
    insert_into_lesson,
    list_available_subs,
    make_lecturer,
    send_num_of_classes,
    update_command,
)
from handlers.cancel import cancel, sub_cancel
from handlers.lesson import (
    available_lessons_button,
    cancel_lesson,
    show_lessons,
    show_my_lessons,
    subscribe_to_lesson,
    user_lessons_button,
)
from handlers.register import REGISTER, register_command, register_user
from handlers.start import ACTIVATE_KEY, START, start_command
from services.filters import (
    ADMIN_AND_PRIVATE_FILTER,
    ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
    ADMIN_FILTER,
)
from services.filters import PRIVATE_CHAT_FILTER


REGISTER_USER_HANDLER = ConversationHandler(
    [
        MessageHandler(
            filters.Regex("^Регистрация$") & PRIVATE_CHAT_FILTER, register_command
        )
    ],
    states={
        REGISTER: [
            MessageHandler(
                filters.TEXT
                & PRIVATE_CHAT_FILTER
                & filters.Regex("^(?!cancel$)(?!Отменить$)(?!\/cancel$).+"),
                register_user,
            )
        ]
    },
    fallbacks=[
        CommandHandler(["cancel"], sub_cancel, filters=PRIVATE_CHAT_FILTER),
        MessageHandler(filters.Regex("cancel") & PRIVATE_CHAT_FILTER, sub_cancel),
    ],
    map_to_parent={ConversationHandler.END: START},
)

START_HANDLER = ConversationHandler(
    entry_points=[
        CommandHandler(["start"], start_command, filters=PRIVATE_CHAT_FILTER),
    ],
    states={
        START: [
            MessageHandler(
                filters.Regex("^Доступные занятия$") & PRIVATE_CHAT_FILTER, show_lessons
            ),
            MessageHandler(
                filters.Regex("^Мои занятия$") & PRIVATE_CHAT_FILTER, show_my_lessons
            ),
            MessageHandler(
                filters.Regex("^Активировать ключ$") & PRIVATE_CHAT_FILTER,
                activate_key_command,
            ),
            MessageHandler(
                filters.Regex("^Оставшееся количество занятий$") & PRIVATE_CHAT_FILTER,
                show_number_of_remaining_classes_on_subscription,
            ),
            REGISTER_USER_HANDLER,
        ],
        ACTIVATE_KEY: [
            MessageHandler(
                filters=PRIVATE_CHAT_FILTER
                & filters.Regex("^(?!cancel$)(?!Отменить$)(?!\/cancel$).+"),
                callback=register_sub_key_to_user,
            )
        ],
    },
    fallbacks=[
        CommandHandler(["cancel"], cancel, filters=PRIVATE_CHAT_FILTER),
        MessageHandler(
            filters.Regex("^(cancel|Отменить)$") & PRIVATE_CHAT_FILTER, cancel
        ),
    ],
)

# REGISTER_USER_HANDLER = ConversationHandler(
#     [CommandHandler(["register"], register_command, filters=private_chat_filter)],
#     states={
#         REGISTER: [MessageHandler(filters.TEXT & private_chat_filter, register_user)]
#     },
#     fallbacks=[
#         CommandHandler(["cancel"], cancel, filters=private_chat_filter),
#         MessageHandler(filters.Regex("cancel") & private_chat_filter, cancel),
#     ],
# )


ADMIN_HANDLER = ConversationHandler(
    [CommandHandler("admin", admin_command, filters=ADMIN_AND_PRIVATE_FILTER)],
    {
        CHOOSING: [
            MessageHandler(
                filters.Regex("^Создать ключ$") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                generate_sub,
            ),
            MessageHandler(
                filters.Regex("^Доступные ключи$")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                list_available_subs,
            ),
            MessageHandler(
                filters.Regex("^Обновить уроки$")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                update_command,
            ),
            MessageHandler(
                filters.Regex("^Добавить преподователя$")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                enter_lecturer_phone_number,
            ),
        ],
        GET_CSV_FILE: [
            MessageHandler(
                filters.Document.MimeType("text/csv")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                insert_into_lesson,
            ),
        ],
        LECTURER_PHONE: [
            MessageHandler(
                filters.Regex("^[8][0-9]{10}$") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                make_lecturer,
            )
        ],
        NUM_OF_CLASSES: [
            MessageHandler(
                filters.Regex("\d+") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                send_num_of_classes,
            )
        ],
    },
    [
        CommandHandler(["cancel"], cancel, filters=ADMIN_AND_PRIVATE_FILTER),
        MessageHandler(
            filters=filters.Regex("cancel") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
            callback=cancel,
        ),
    ],
)

CQH_SUBSCRIBE_LESSON = CallbackQueryHandler(
    subscribe_to_lesson, pattern="^" + config.CALLBACK_LESSON_PATTERN + "subscribe$"
)

CQH_CANCEL_LESSON = CallbackQueryHandler(
    cancel_lesson, pattern="^" + config.CALLBACK_USER_LESSON_PATTERN + "cancel$"
)

CQH_LESSON_BUTTONS = CallbackQueryHandler(
    available_lessons_button, pattern="^" + config.CALLBACK_LESSON_PATTERN
)
CQH_USER_LESSON_BUTTONS = CallbackQueryHandler(
    user_lessons_button, pattern="^" + config.CALLBACK_USER_LESSON_PATTERN
)

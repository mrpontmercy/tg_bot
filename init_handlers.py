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
    admin_command,
    enter_lecturer_phone_number,
    generate_sub,
    insert_into_lesson,
    list_available_subs,
    make_lecturer,
    make_new_subscription,
    return_to_start_command,
    subs_button,
    update_command,
)
from handlers.cancel import cancel, sub_cancel
from handlers.confirmation import (
    cancel_action_button,
    confirm_action,
    confirmation_action_handler,
)
from handlers.lesson import (
    available_lessons_button,
    lecturer_lessons_button,
    show_lecturer_lessons,
    show_lessons,
    show_my_lessons,
    user_lessons_button,
)
from handlers.register import REGISTER, register_command, register_user
from handlers.start import start_command
from services.filters import (
    ADMIN_AND_PRIVATE_FILTER,
    ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
)
from services.filters import PRIVATE_CHAT_FILTER
from services.states import AdminStates, StartHandlerStates

CQH_CONFIRM_SUBSCRIBE = CallbackQueryHandler(
    confirmation_action_handler,
    pattern=f".*({config.CALLBACK_DATA_SUBSCRIBE}|{config.CALLBACK_DATA_CANCEL_LESSON}|{config.CALLBACK_DATA_DELETESUBSCRIPTION}|{config.CALLBACK_DATA_DELETE_LESSON})$",
)

CQH_CONFIRM_SUBCRIBE_YES = CallbackQueryHandler(
    confirm_action, pattern=".*_confirm_action$"
)

CQH_CONFIRM_SUBCRIBE_CANCEL = CallbackQueryHandler(
    cancel_action_button, pattern=".*_cancel_action$"
)

CQH_LESSON_BUTTONS = CallbackQueryHandler(
    available_lessons_button, pattern="^" + config.CALLBACK_LESSON_PREFIX + "\d+"
)
CQH_USER_LESSON_BUTTONS = CallbackQueryHandler(
    user_lessons_button, pattern="^" + config.CALLBACK_USER_LESSON_PREFIX + "\d+"
)

CQH_LECTURER_CANCEL_LESSON_BUTTONS = CallbackQueryHandler(
    lecturer_lessons_button,
    pattern="^" + config.CALLBACK_LECTURER_LESSON_PREFIX + "\d+",
)

CQH_AVAILABLE_SUBS_BUTTONS = CallbackQueryHandler(
    subs_button, pattern="^" + config.CALLBACK_SUB_PREFIX + "\d+"
)

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
    map_to_parent={
        ConversationHandler.END: StartHandlerStates.START,
    },
)

ADMIN_HANDLER_2 = ConversationHandler(
    [
        MessageHandler(
            filters.Regex("^Админ панель$") & ADMIN_AND_PRIVATE_FILTER,
            admin_command,
        ),
    ],
    {
        AdminStates.CHOOSING: [
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
            MessageHandler(
                filters.Regex("^Назад$") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                return_to_start_command,
            ),
        ],
        AdminStates.GET_CSV_FILE: [
            MessageHandler(
                filters.Document.MimeType("text/csv")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                insert_into_lesson,
            ),
        ],
        AdminStates.LECTURER_PHONE: [
            MessageHandler(
                filters.TEXT
                & filters.Regex("^(?!Назад$).+")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                make_lecturer,
            )
        ],
        AdminStates.NUM_OF_CLASSES: [
            MessageHandler(
                filters.TEXT
                & filters.Regex("^(?!Назад$).+")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                make_new_subscription,
            )
        ],
    },
    [
        MessageHandler(
            filters.Regex("^Назад$") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
            return_to_start_command,
        ),
    ],
    map_to_parent={ConversationHandler.END, StartHandlerStates.START},
)


START_HANDLER = ConversationHandler(
    entry_points=[
        CommandHandler(["start"], start_command, filters=PRIVATE_CHAT_FILTER),
    ],
    states={
        StartHandlerStates.START: [
            MessageHandler(
                filters.Regex("^Доступные занятия$") & PRIVATE_CHAT_FILTER,
                show_lessons,
            ),
            MessageHandler(
                filters.Regex("^Мои занятия$") & PRIVATE_CHAT_FILTER,
                show_my_lessons,
            ),
            MessageHandler(
                filters.Regex("^Активировать ключ$") & PRIVATE_CHAT_FILTER,
                activate_key_command,
            ),
            MessageHandler(
                filters.Regex("^Оставшееся количество занятий$") & PRIVATE_CHAT_FILTER,
                show_number_of_remaining_classes_on_subscription,
            ),
            MessageHandler(
                filters.Regex("^Ваши занятия$") & PRIVATE_CHAT_FILTER,
                show_lecturer_lessons,
            ),
            REGISTER_USER_HANDLER,
            ADMIN_HANDLER_2,
        ],
        StartHandlerStates.ACTIVATE_KEY: [
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

ADMIN_HANDLER = ConversationHandler(
    [CommandHandler("admin", admin_command, filters=ADMIN_AND_PRIVATE_FILTER)],
    {
        AdminStates.CHOOSING: [
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
        AdminStates.GET_CSV_FILE: [
            MessageHandler(
                filters.Document.MimeType("text/csv")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                insert_into_lesson,
            ),
        ],
        AdminStates.LECTURER_PHONE: [
            MessageHandler(
                filters.TEXT
                & filters.Regex("^(?!cancel$)(?!Отменить$)(?!\/cancel$).+")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                make_lecturer,
            )
        ],
        AdminStates.NUM_OF_CLASSES: [
            MessageHandler(
                filters.TEXT
                & filters.Regex("^(?!cancel$)(?!Отменить$)(?!\/cancel$).+")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                make_new_subscription,
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

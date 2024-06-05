from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
import config
from handlers.lecturer.lecturer import (
    begin_edit_lesson,
    edit_num_of_seats_lesson,
    edit_title_lesson,
    edit_time_start_lesson,
    enter_num_of_seats_lesson,
    enter_time_start_lesson,
    enter_title_lesson,
    insert_lessons_from_file_lecturer,
    lecturer_lessons_button,
    send_file_lessons_lecturer,
    show_lecturer_lessons,
)
from handlers.student.subscription import (
    activate_subkey_command,
    register_sub_key_to_user,
    show_number_of_remaining_classes_on_subscription,
)
from handlers.admin.admin import (
    admin_command,
    enter_lecturer_phone_number,
    generate_sub,
    insert_lesson_handler,
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
from handlers.student.lesson import (
    available_lessons_button,
    show_lessons,
    show_my_lessons,
    user_lessons_button,
)
from handlers.register.register import REGISTER, register_command, register_user
from handlers.begin import start_command
from services.filters import (
    ADMIN_AND_PRIVATE_FILTER,
    ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
)
from services.filters import PRIVATE_CHAT_FILTER
from services.states import AdminState, EditLessonState, StartHandlerState

CQH_CONFIRM_SUBSCRIBE = CallbackQueryHandler(
    confirmation_action_handler,
    pattern=f".*({config.CALLBACK_DATA_SUBSCRIBE}|{config.CALLBACK_DATA_CANCEL_LESSON}|{config.CALLBACK_DATA_DELETESUBSCRIPTION}|{config.CALLBACK_DATA_CANCEL_LESSON_LECTURER})$",
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

CQH_LECTURER_LESSON_BUTTONS = CallbackQueryHandler(
    lecturer_lessons_button,
    pattern="^" + config.CALLBACK_LECTURER_LESSON_PREFIX + "\d+",
)

CQH_LECTURER_START_EDIT_LESSON_BUTTONS = CallbackQueryHandler(
    begin_edit_lesson,
    pattern="^"
    + config.CALLBACK_LECTURER_LESSON_PREFIX
    + config.CALLBACK_DATA_EDIT_LESSON
    + "$",
)

CQH_LECTURER_EDIT_LESSON_BUTTONS = CallbackQueryHandler(
    begin_edit_lesson,
    pattern="^"
    + config.CALLBACK_LECTURER_LESSON_PREFIX
    + "(editTitle|editTimeStart)"
    + "$",
)

CQH_AVAILABLE_SUBS_BUTTONS = CallbackQueryHandler(
    subs_button,
    pattern="^" + config.CALLBACK_SUB_PREFIX + "\d+",
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
        ConversationHandler.END: StartHandlerState.START,
    },
)

ADMIN_HANDLER = ConversationHandler(
    [
        MessageHandler(
            filters.Regex("^Админ панель$") & ADMIN_AND_PRIVATE_FILTER,
            admin_command,
        ),
    ],
    {
        AdminState.CHOOSING: [
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
        AdminState.GET_CSV_FILE: [
            MessageHandler(
                filters.Document.MimeType("text/csv")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                insert_lesson_handler,
            ),
        ],
        AdminState.LECTURER_PHONE: [
            MessageHandler(
                filters.TEXT
                & filters.Regex("^(?!Назад$).+")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                make_lecturer,
            )
        ],
        AdminState.NUM_OF_CLASSES: [
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
    map_to_parent={ConversationHandler.END, StartHandlerState.START},
)


EDIT_LESSON_HANDLER = ConversationHandler(
    [CQH_LECTURER_START_EDIT_LESSON_BUTTONS],
    states={
        EditLessonState.CHOOSE_OPTION: [
            MessageHandler(
                filters.Regex("^Изменить заголовок$")
                & PRIVATE_CHAT_FILTER
                & ~filters.Regex("^Назад$"),
                enter_title_lesson,
            ),
            MessageHandler(
                filters.Regex("^Изменить дату и время$")
                & PRIVATE_CHAT_FILTER
                & ~filters.Regex("^Назад$"),
                enter_time_start_lesson,
            ),
            MessageHandler(
                filters.Regex("^Изменить количество доступных мест$")
                & PRIVATE_CHAT_FILTER
                & ~filters.Regex("^Назад$"),
                enter_num_of_seats_lesson,
            ),
        ],
        EditLessonState.EDIT_TITLE: [
            MessageHandler(
                filters.TEXT & PRIVATE_CHAT_FILTER & ~filters.Regex("^Назад$"),
                edit_title_lesson,
            )
        ],
        EditLessonState.EDIT_TIMESTART: [
            MessageHandler(
                filters.TEXT & PRIVATE_CHAT_FILTER & ~filters.Regex("^Назад$"),
                edit_time_start_lesson,
            )
        ],
        EditLessonState.EDIT_NUM_OF_SEATS: [
            MessageHandler(
                filters.TEXT & PRIVATE_CHAT_FILTER & ~filters.Regex("^Назад$"),
                edit_num_of_seats_lesson,
            )
        ],
    },
    fallbacks=[
        MessageHandler(
            filters.Regex("^Назад$") & PRIVATE_CHAT_FILTER & ~filters.COMMAND,
            return_to_start_command,
        ),
    ],
    map_to_parent={ConversationHandler.END, StartHandlerState.START},
)

START_HANDLER = ConversationHandler(
    entry_points=[
        CommandHandler(["start"], start_command, filters=PRIVATE_CHAT_FILTER),
    ],
    states={
        StartHandlerState.START: [
            MessageHandler(
                filters.Regex("^Доступные занятия$") & PRIVATE_CHAT_FILTER,
                show_lessons,
            ),
            MessageHandler(
                filters.Regex("^Мои занятия$") & PRIVATE_CHAT_FILTER,
                show_my_lessons,
            ),
            MessageHandler(
                filters.Regex("^Добавить занятия$") & PRIVATE_CHAT_FILTER,
                send_file_lessons_lecturer,
            ),
            MessageHandler(
                filters.Regex("^Активировать ключ$") & PRIVATE_CHAT_FILTER,
                activate_subkey_command,
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
            ADMIN_HANDLER,
            EDIT_LESSON_HANDLER,
        ],
        StartHandlerState.ACTIVATE_KEY: [
            MessageHandler(
                filters=PRIVATE_CHAT_FILTER
                & filters.Regex("^(?!cancel$)(?!Отменить$)(?!\/cancel$).+"),
                callback=register_sub_key_to_user,
            )
        ],
        StartHandlerState.SEND_FILE_LESSONS_LECTURER: [
            MessageHandler(
                filters.Document.MimeType("text/csv") & PRIVATE_CHAT_FILTER,
                insert_lessons_from_file_lecturer,
            ),
        ],
    },
    fallbacks=[
        CommandHandler(["cancel"], cancel, filters=PRIVATE_CHAT_FILTER),
        MessageHandler(
            filters.Regex("^(cancel|Отменить)$") & PRIVATE_CHAT_FILTER, cancel
        ),
    ],
)

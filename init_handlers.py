from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from config import (
    CALLBACK_DATA_CANCEL_LESSON,
    CALLBACK_DATA_CANCEL_LESSON_LECTURER,
    CALLBACK_DATA_DELETESUBSCRIPTION,
    CALLBACK_DATA_SUBSCRIBE,
    CALLBACK_LESSON_PREFIX,
    CALLBACK_SUB_PREFIX,
)
from handlers.admin.admin import (
    admin_command,
    end_admin_conv,
    enter_lecturer_phone_number,
    generate_sub,
    insert_lesson_handler,
    list_available_subs,
    make_lecturer,
    make_new_subscription,
    return_to_start_command,
    send_lessons_file,
    subs_button,
)
from handlers.confirmation import (
    cancel_action_button,
    confirm_action,
    confirmation_action_handler,
)
from handlers.create_conv_handler import (
    create_hanlder,
    return_back_admin,
    return_back_start,
)
from handlers.lecturer.lecturer import (
    edit_title_lesson,
)
from handlers.lecturer.new_lecturer import start_editing_lesson
from handlers.student.subscription import (
    register_sub_key_to_user,
    show_number_of_remaining_classes_on_subscription,
    start_activating_subkey,
)
from handlers.cancel import cancel
from handlers.student.lesson import (
    available_lessons_button,
    show_lessons,
    show_my_lessons,
)
from handlers.register.register import (
    start_register_action,
    register_user,
)
from handlers.start import start_command, stop, stop_command
from services.filters import ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER, PRIVATE_CHAT_FILTER
from services.states import (
    END,
    AdminState,
    EditLessonState,
    RegisterState,
    StartHandlerState,
)

CQH_CONFIRM_SUBSCRIBE = CallbackQueryHandler(
    confirmation_action_handler,
    pattern=f".*({CALLBACK_DATA_SUBSCRIBE}|{CALLBACK_DATA_CANCEL_LESSON}|{CALLBACK_DATA_DELETESUBSCRIPTION}|{CALLBACK_DATA_CANCEL_LESSON_LECTURER})$",
)

CQH_CONFIRM_SUBCRIBE_YES = CallbackQueryHandler(
    confirm_action, pattern=".*_confirm_action$"
)

CQH_CONFIRM_SUBCRIBE_CANCEL = CallbackQueryHandler(
    cancel_action_button, pattern=".*_cancel_action$"
)

# CQH_LESSON_BUTTONS = CallbackQueryHandler(
#     available_lessons_button, pattern="^" + CALLBACK_LESSON_PREFIX + "\d+"
# )
# CQH_USER_LESSON_BUTTONS = CallbackQueryHandler(
#     user_lessons_button, pattern="^" + config.CALLBACK_USER_LESSON_PREFIX + "\d+"
# )

# CQH_LECTURER_LESSON_BUTTONS = CallbackQueryHandler(
#     lecturer_lessons_button,
#     pattern="^" + config.CALLBACK_LECTURER_LESSON_PREFIX + "\d+",
# )

# CQH_LECTURER_START_EDIT_LESSON_BUTTONS = CallbackQueryHandler(
#     begin_edit_lesson,
#     pattern="^"
#     + config.CALLBACK_LECTURER_LESSON_PREFIX
#     + config.CALLBACK_DATA_EDIT_LESSON
#     + "$",
# )

# CQH_AVAILABLE_SUBS_BUTTONS = CallbackQueryHandler(
#     subs_button,
#     pattern="^" + config.CALLBACK_SUB_PREFIX + "\d+",
# )

# REGISTER_USER_HANDLER = ConversationHandler(
#     [
#         MessageHandler(
#             filters.Regex("^Регистрация$") & PRIVATE_CHAT_FILTER, start_reggister_action
#         )
#     ],
#     states={
#         REGISTER: [
#             MessageHandler(
#                 filters.TEXT
#                 & PRIVATE_CHAT_FILTER
#                 & filters.Regex("^(?!cancel$)(?!Отменить$)(?!\/cancel$).+"),
#                 register_user,
#             )
#         ]
#     },
#     fallbacks=[
#         CommandHandler(["cancel"], sub_cancel, filters=PRIVATE_CHAT_FILTER),
#         MessageHandler(filters.Regex("cancel") & PRIVATE_CHAT_FILTER, sub_cancel),
#     ],
#     map_to_parent={
#         ConversationHandler.END: StartHandlerState.START,
#     },
# )

# ADMIN_HANDLER = ConversationHandler(
#     [
#         MessageHandler(
#             filters.Regex("^Админ панель$") & ADMIN_AND_PRIVATE_FILTER,
#             admin_command,
#         ),
#     ],
#     {
#         AdminState.CHOOSING: [
#             MessageHandler(
#                 filters.Regex("^Создать ключ$") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
#                 generate_sub,
#             ),
#             MessageHandler(
#                 filters.Regex("^Доступные ключи$")
#                 & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
#                 list_available_subs,
#             ),
#             MessageHandler(
#                 filters.Regex("^Обновить уроки$") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
#                 send_lessons_file,
#             ),
#             MessageHandler(
#                 filters.Regex("^Добавить преподователя$")
#                 & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
#                 enter_lecturer_phone_number,
#             ),
#             MessageHandler(
#                 filters.Regex("^Назад$") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
#                 return_to_start_command,
#             ),
#         ],
#         AdminState.GET_CSV_FILE: [
#             MessageHandler(
#                 filters.Document.MimeType("text/csv")
#                 & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
#                 insert_lesson_handler,
#             ),
#         ],
#         AdminState.LECTURER_PHONE: [
#             MessageHandler(
#                 filters.TEXT
#                 & filters.Regex("^(?!Назад$).+")
#                 & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
#                 make_lecturer,
#             )
#         ],
#         AdminState.NUM_OF_CLASSES: [
#             MessageHandler(
#                 filters.TEXT
#                 & filters.Regex("^(?!Назад$).+")
#                 & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
#                 make_new_subscription,
#             )
#         ],
#     },
#     [
#         MessageHandler(
#             filters.Regex("^Назад$") & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
#             return_to_start_command,
#         ),
#     ],
#     map_to_parent={ConversationHandler.END, StartHandlerState.START},
# )


# EDIT_LESSON_HANDLER = ConversationHandler(
#     [CQH_LECTURER_START_EDIT_LESSON_BUTTONS],
#     states={
#         EditLessonState.CHOOSE_OPTION: [
#             MessageHandler(
#                 filters.Regex("^Изменить заголовок$")
#                 & PRIVATE_CHAT_FILTER
#                 & ~filters.Regex("^Назад$"),
#                 enter_title_lesson,
#             ),
#             MessageHandler(
#                 filters.Regex("^Изменить дату и время$")
#                 & PRIVATE_CHAT_FILTER
#                 & ~filters.Regex("^Назад$"),
#                 enter_time_start_lesson,
#             ),
#             MessageHandler(
#                 filters.Regex("^Изменить количество доступных мест$")
#                 & PRIVATE_CHAT_FILTER
#                 & ~filters.Regex("^Назад$"),
#                 enter_num_of_seats_lesson,
#             ),
#         ],
#         EditLessonState.EDIT_TITLE: [
#             MessageHandler(
#                 filters.TEXT & PRIVATE_CHAT_FILTER & ~filters.Regex("^Назад$"),
#                 edit_title_lesson,
#             )
#         ],
#         EditLessonState.EDIT_TIMESTART: [
#             MessageHandler(
#                 filters.TEXT & PRIVATE_CHAT_FILTER & ~filters.Regex("^Назад$"),
#                 edit_time_start_lesson,
#             )
#         ],
#         EditLessonState.EDIT_NUM_OF_SEATS: [
#             MessageHandler(
#                 filters.TEXT & PRIVATE_CHAT_FILTER & ~filters.Regex("^Назад$"),
#                 edit_num_of_seats_lesson,
#             )
#         ],
#     },
#     fallbacks=[
#         MessageHandler(
#             filters.Regex("^Назад$") & PRIVATE_CHAT_FILTER & ~filters.COMMAND,
#             return_to_start_command,
#         ),
#     ],
#     map_to_parent={ConversationHandler.END, StartHandlerState.START},
# )

conv_handler2 = ConversationHandler(
    [
        CallbackQueryHandler(
            start_editing_lesson, pattern=f"^{EditLessonState.CHOOSE_OPTION}$"
        )
    ],
    states={EditLessonState.EDIT_TITLE: [edit_title_lesson]},
    fallbacks=[CommandHandler(["cancel"], cancel, filters=PRIVATE_CHAT_FILTER)],
)

REGISTER_USER = ConversationHandler(
    [
        CallbackQueryHandler(
            start_register_action, pattern=f"^{RegisterState.START_REGISTER}$"
        )
    ],
    states={
        RegisterState.REGISTER: [
            MessageHandler(
                filters.TEXT
                & PRIVATE_CHAT_FILTER
                & filters.Regex("^(?!\/stop$)(?!cancel$)(?!Отменить$)(?!\/cancel$).+"),
                register_user,
            )
        ]
    },
    fallbacks=[CommandHandler("stop", stop_command)],
    map_to_parent={
        END: StartHandlerState.SELECTING_ACTION,
    },
)

SUBS_FLIP_HANLDER = create_hanlder(
    list_available_subs,
    subs_button,
    AdminState.LIST_AVAILABLE_SUBS,
    CALLBACK_SUB_PREFIX,
    AdminState.CHOOSING,
    return_back_admin,
)

admin_selective_handlers = [
    CallbackQueryHandler(generate_sub, pattern=f"^{AdminState.GENERATE_SUB}$"),
    CallbackQueryHandler(send_lessons_file, pattern=f"^{AdminState.UPDATE_LESSONS}$"),
    CallbackQueryHandler(
        enter_lecturer_phone_number, pattern=f"^{AdminState.ADD_LECTURER}$"
    ),
    SUBS_FLIP_HANLDER,
]


ADMIN_HANDLER = ConversationHandler(
    [
        CallbackQueryHandler(
            admin_command,
            pattern=f"^{AdminState.START_ADMIN}$",
        ),
    ],
    states={
        AdminState.CHOOSING: admin_selective_handlers,
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
        AdminState.GET_NUM_OF_CLASSES: [
            MessageHandler(
                filters.TEXT
                & filters.Regex("^(?!Назад$).+")
                & ADMIN_AND_PRIVATE_NOT_COMMAND_FILTER,
                make_new_subscription,
            )
        ],
    },
    fallbacks=[
        CommandHandler("stop", stop_command),
        CallbackQueryHandler(end_admin_conv, pattern=f"^{END}$"),
    ],
    map_to_parent={END, StartHandlerState.SELECTING_ACTION},
)

USER_UPCOMING_LESSONS_HANDLER = create_hanlder(
    show_lessons,
    available_lessons_button,
    StartHandlerState.SHOW_UPCOMING_LESSONS,
    CALLBACK_LESSON_PREFIX,
    StartHandlerState.SELECTING_ACTION,
    return_back_start,
)

selection_handlers = [
    CallbackQueryHandler(
        show_my_lessons, pattern=f"^{StartHandlerState.SHOW_MY_LESSONS}$"
    ),
    CallbackQueryHandler(
        start_activating_subkey, pattern=f"^{StartHandlerState.START_ACTIVATE_KEY}$"
    ),
    CallbackQueryHandler(
        show_number_of_remaining_classes_on_subscription,
        pattern=f"^{StartHandlerState.SHOW_REMAINING_CLASSES}$",
    ),
    REGISTER_USER,
    ADMIN_HANDLER,
    USER_UPCOMING_LESSONS_HANDLER,
]

# MessageHandler(
#     filters.Regex("^Доступные занятия$") & PRIVATE_CHAT_FILTER,
#     show_lessons,
# ),
# MessageHandler(
#     filters.Regex("^Мои занятия$") & PRIVATE_CHAT_FILTER,
#     show_my_lessons,
# ),
# MessageHandler(
#     filters.Regex("^Добавить занятия$") & PRIVATE_CHAT_FILTER,
#     send_file_lessons_lecturer,
# ),
# MessageHandler(
#     filters.Regex("^Активировать ключ$") & PRIVATE_CHAT_FILTER,
#     activate_subkey_command,
# ),
# MessageHandler(
#     filters.Regex("^Оставшееся количество занятий$") & PRIVATE_CHAT_FILTER,
#     show_number_of_remaining_classes_on_subscription,
# ),
# MessageHandler(
#     filters.Regex("^Ваши занятия$") & PRIVATE_CHAT_FILTER,
#     show_lecturer_lessons,
# ),
# StartHandlerState.ACTIVATE_KEY: [
#     MessageHandler(
#         filters=PRIVATE_CHAT_FILTER
#         & filters.Regex("^(?!cancel$)(?!Отменить$)(?!\/cancel$).+"),
#         callback=register_sub_key_to_user,
#     )
# ],
# StartHandlerState.SEND_FILE_LESSONS_LECTURER: [
#     MessageHandler(
#         filters.Document.MimeType("text/csv") & PRIVATE_CHAT_FILTER,
#         insert_lessons_from_file_lecturer,
#     ),
# ],

START_HANDLER = ConversationHandler(
    entry_points=[
        CommandHandler(["start"], start_command, filters=PRIVATE_CHAT_FILTER),
    ],
    states={
        StartHandlerState.SHOWING: [
            CallbackQueryHandler(start_command, pattern=f"^{END}$"),
            CallbackQueryHandler(
                start_activating_subkey,
                pattern=f"^{StartHandlerState.START_ACTIVATE_KEY}$",
            ),
        ],
        StartHandlerState.SELECTING_ACTION: selection_handlers,
        StartHandlerState.ACTIVATE_KEY: [
            MessageHandler(
                filters=PRIVATE_CHAT_FILTER
                & filters.Regex("^(?!cancel$)(?!Отменить$)(?!\/cancel$).+"),
                callback=register_sub_key_to_user,
            )
        ],
    },
    fallbacks=[
        CommandHandler(["stop"], stop),
        CallbackQueryHandler(cancel, pattern=f"^{END}$"),
    ],
)

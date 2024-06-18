from enum import Enum, auto

from telegram.ext import ConversationHandler

END = ConversationHandler.END


class FlipKBState(Enum):
    START = auto()


class RegisterState(Enum):
    START_REGISTER = auto()
    REGISTER = auto()


class StartHandlerConstants(Enum): ...


class StartHandlerState(Enum):
    # Какой-то мета стейт
    SHOWING = auto()

    SELECTING_ACTION = auto()
    REGISTER = auto()
    SEND_SUBKEY = auto()
    START_ACTIVATE_KEY = auto()
    ACTIVATE_KEY = auto()
    SHOW_UPCOMING_LESSONS = auto()
    SHOW_MY_LESSONS = auto()
    SHOW_REMAINING_CLASSES = auto()
    SEND_FILE_LESSONS_LECTURER = auto()
    CHOOSING_LESSON = auto()
    CONFIRM_ACTION = auto()


class ConfirmState(Enum):
    CONFIRMATION = auto()
    CONFIRM = auto()
    CANCEL = auto()


class AdminState(Enum):
    START_ADMIN = auto()
    CHOOSING = auto()
    GENERATE_SUB = auto()
    GET_NUM_OF_CLASSES = auto()
    LIST_AVAILABLE_SUBS = auto()
    UPDATE_LESSONS = auto()
    GET_CSV_FILE = auto()
    ADD_LECTURER = auto()
    LECTURER_PHONE = auto()


class EditLessonState(Enum):
    CHOOSE_OPTION = auto()
    EDIT_TITLE = auto()
    EDIT_TIMESTART = auto()
    EDIT_NUM_OF_SEATS = auto()

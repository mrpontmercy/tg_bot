from enum import Enum, auto
from telegram.ext import ConversationHandler


END = ConversationHandler.END


class InterimStartState(Enum):
    START_REGISTER = auto()
    START_ACTIVATE_SUBSCRIPTION = auto()
    SHOW_REMAINDER_SUBSCRIPTION = auto()
    SHOW_AVAILABLE_LESSONS = auto()
    SHOW_SCHEDULE_LESSONS = auto()
    BACK_TO_START = auto()


class InterimAdminState(Enum):
    START_GENERATE_SUB = auto()
    LIST_AVAILABLE_SUBS = auto()
    START_UPDATE_LESSONS = auto()
    SHOW_ALL_LESSONS = auto()
    EDIT_LESSON = auto()
    ENTER_LECTURER_PHONE = auto()
    BACK_TO_ADMIN = auto()


class StartState(Enum):
    SHOWING = auto()
    CHOOSE_ACTION = auto()
    ACTIVATE_SUBSCRIPTION = auto()
    REGISTRATION = auto()
    ACTIVETE_SUBSCRIPTION = auto()


class AdminState(Enum):
    CHOOSE_ACTION = auto()
    GENERATE_SUB = auto()
    ADD_LECTURER = auto()
    INSERT_LESSONS = auto()


class SwitchState(Enum):
    CHOOSE_ACTION = auto()
    RETURN_PREV_CONV = auto()


class EditLesson(Enum):
    CHOOSE_ACTION = auto()
    EDIT_TITLE = auto()
    EDIT_TIMESTART = auto()
    EDIT_NUM_OF_SEATS = auto()
    EDIT_LESSON_LINK = auto()
    RETURN_PREV_CONV = auto()


class InterimEditLesson(Enum):
    START_EDIT_LESSON = auto()
    START_EDIT_TITLE = auto()
    START_EDIT_TIMESTART = auto()
    START_EDIT_NUM_OF_SEATS = auto()
    START_EDIT_LESSON_LINK = auto()

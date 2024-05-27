from enum import Enum, auto


class StartHandlerState(Enum):
    START = auto()
    ACTIVATE_KEY = auto()
    CHOOSING_LESSON = auto()
    CONFIRM_ACTION = auto()


class ConfirmState(Enum):
    CONFIRMATION = auto()
    CONFIRM = auto()
    CANCEL = auto()


class AdminState(Enum):
    CHOOSING = auto()
    GET_CSV_FILE = auto()
    LECTURER_PHONE = auto()
    NUM_OF_CLASSES = auto()


class EditLessonState(Enum):
    CHOOSE_OPTION = auto()
    EDIT_TITLE = auto()
    EDIT_TIMESTART = auto()

from enum import Enum, auto


class StartHandlerStates(Enum):
    START = auto()
    ACTIVATE_KEY = auto()
    CHOOSING_LESSON = auto()
    CONFIRM_ACTION = auto()


class ConfirmStates(Enum):
    CONFIRMATION = auto()
    CONFIRM = auto()
    CANCEL = auto()


class AdminStates(Enum):
    CHOOSING = auto()
    GET_CSV_FILE = auto()
    LECTURER_PHONE = auto()
    NUM_OF_CLASSES = auto()

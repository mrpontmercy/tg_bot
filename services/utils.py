from dataclasses import dataclass, field
from functools import wraps
import re
from typing import Any

from services.exceptions import ColumnCSVError


PHONE_NUMBER_PATTERN = r"^[8][0-9]{10}$"  # Для российских номеров
FS_NAME_PATTERN = r"^[a-zA-Zа-яёА-ЯЁ]{3,}$"
EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
DATE_TIME_PATTERN = r"^\d{4}-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01]) (0?[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"


@dataclass
class User:
    telegram_id: int
    username: str
    f_name: str
    s_name: str
    phone_number: str
    email: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "f_name": self.f_name,
            "s_name": self.s_name,
            "phone_number": self.phone_number,
            "email": self.email,
        }


@dataclass
class UserID(User):
    id: int
    status: str = field(default="Студент")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "f_name": self.f_name,
            "s_name": self.s_name,
            "phone_number": self.phone_number,
            "email": self.email,
            "status": self.status,
        }


@dataclass
class Subscription:
    id: int
    sub_key: int
    num_of_classes: int
    user_id: int | None

    def to_dict(self):
        return {
            "id": self.id,
            "sub_key": self.sub_key,
            "num_of_classes": self.num_of_classes,
            "user_id": self.user_id,
        }


@dataclass
class TransientLesson:
    title: str
    time_start: str
    num_of_seats: str
    lecturer_phone: str | None = None

    def __post_init__(self):
        if self.lecturer_phone is not None and not re.fullmatch(
            PHONE_NUMBER_PATTERN, self.lecturer_phone
        ):
            raise ColumnCSVError("Неверно заполнены столбцы!")
        elif not re.fullmatch(DATE_TIME_PATTERN, self.time_start):
            raise ColumnCSVError("Неверно заполнены столбцы!")

    def to_dict(self):
        return {
            "title": self.title,
            "time_start": self.time_start,
            "num_of_seats": self.num_of_seats,
            "lecturer_phone": self.lecturer_phone,
        }


@dataclass
class Lesson:
    id: str | int
    title: str
    time_start: str
    num_of_seats: str | int
    lecturer_full_name: str
    lecturer_id: str | int

    def __post_init__(self):
        isinstances = [
            isinstance(self.title, str),
            isinstance(self.time_start, str),
            isinstance(self.num_of_seats, (str, int)),
            isinstance(self.lecturer_full_name, str),
            isinstance(self.lecturer_id, (str, int)),
        ]
        if not all(isinstances):
            raise ColumnCSVError("Неверно заполнены столбцы!")

    def to_dict(self):
        result: dict[str, str | int] = {
            "id": self.id,
            "title": self.title,
            "time_start": self.time_start,
            "num_of_seats": self.num_of_seats,
            "lecturer": self.lecturer_full_name,
            "lecturer_id": self.lecturer_id,
        }

        return result

    def to_dict_lesson_info(self):
        return {
            "title": self.title,
            "time_start": self.time_start,
            "num_of_seats": self.num_of_seats,
            "lecturer_full_name": self.lecturer_full_name,
        }


# позволяет переиспользовать start_command без вывода приветственного сообщения
def add_start_over(func):
    @wraps(func)
    async def wrapper(update, context):
        context.user_data["START_OVER"] = True
        return await func(update, context)

    return wrapper


def add_message_info_into_context(func):
    @wraps(func)
    async def wrapper(update, context):
        context.user_data["delete_message_info"] = (
            update.effective_chat.id,
            update.effective_message.id,
        )
        return await func(update, context)

    return wrapper


async def delete_last_message_from_context(context):
    del_info = context.user_data.get("delete_message_info")
    if del_info:
        await context.bot.delete_message(del_info[0], del_info[1])

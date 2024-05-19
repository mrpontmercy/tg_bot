from dataclasses import dataclass
from typing import Any

from services.exceptions import ColumnCSVError


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "f_name": self.f_name,
            "s_name": self.s_name,
            "phone_number": self.phone_number,
            "email": self.email,
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
class Lesson:
    id: str | int
    title: str
    time_start: str
    num_of_seats: str | int
    lecturer: str
    tg_id_lecturer: str | int

    def __post_init__(self):
        isinstances = [
            isinstance(self.id, (str, int)),
            isinstance(self.title, str),
            isinstance(self.time_start, str),
            isinstance(self.num_of_seats, (str, int)),
            isinstance(self.lecturer, str),
            isinstance(self.tg_id_lecturer, (str, int)),
        ]
        if not all(isinstances):
            raise ColumnCSVError("Неверно заполнены столбцы!")

    def to_dict(self):
        result: dict[str, str | int] = {
            "id": self.id,
            "title": self.title,
            "time_start": self.time_start,
            "num_of_seats": self.num_of_seats,
            "lecturer": self.lecturer,
            "tg_id_lecturer": self.tg_id_lecturer,
        }

        return result

    def to_dict_lesson_info(self):
        return {
            "title": self.title,
            "time_start": self.time_start,
            "num_of_seats": self.num_of_seats,
            "lecturer": self.lecturer,
        }

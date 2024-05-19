import logging
import re
from typing import Any, Iterable


from services.db import (
    execute_insert,
)
from services.exceptions import (
    ValidationEmailError,
    ValidationFirstNameError,
    ValidationPhoneNumberError,
    ValidationSecondNameError,
    ValidationUserError,
)
from services.utils import User

phone_number_pattern = r"^[8][0-9]{10}$"  # Для российских номеров
name_s_name_patternt = r"^[a-zA-Zа-яА-Я]{3,}$"
email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


def validate_message(input_message: list[str]):
    # обработать строку пользователя
    try:
        validated_message = _validate_user(input_message)
    except (
        ValidationFirstNameError,
        ValidationSecondNameError,
        ValidationUserError,
        ValidationPhoneNumberError,
        ValidationEmailError,
    ) as e:
        logging.getLogger(__name__).exception(e)
        raise
    return validated_message


async def insert_user(params: Iterable[Any]):
    table = "user"
    columns = "telegram_id, username, f_name, s_name, phone_number, email"
    values = ":telegram_id, :username, :f_name, :s_name, :phone_number, :email"
    await execute_insert(table, columns, values, params)


def _validate_user(user_info: list[str]) -> User:
    if len(user_info) != 6:
        raise ValidationUserError
    f_name = user_info[0]
    if not re.fullmatch(name_s_name_patternt, f_name):
        raise ValidationFirstNameError("Неверное имя пользователя")

    s_name = user_info[1]
    if not re.fullmatch(name_s_name_patternt, s_name):
        raise ValidationSecondNameError("Неверная фамилия пользователя")

    phone_number = user_info[2]
    if not re.fullmatch(phone_number_pattern, phone_number):
        raise ValidationPhoneNumberError("Неверный номер пользователя")

    email = user_info[3]
    if not re.fullmatch(email_pattern, email):
        raise ValidationEmailError("Неверный Email!")

    user = User(*user_info)
    return user

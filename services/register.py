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
from services.utils import (
    User,
    EMAIL_PATTERN,
    FS_NAME_PATTERN,
    PHONE_NUMBER_PATTERN,
)


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

    f_name = user_info[2]
    if not re.fullmatch(FS_NAME_PATTERN, f_name):
        raise ValidationFirstNameError("Неверное имя пользователя")

    s_name = user_info[3]
    if not re.fullmatch(FS_NAME_PATTERN, s_name):
        raise ValidationSecondNameError("Неверная фамилия пользователя")

    phone_number = user_info[4]
    if not re.fullmatch(PHONE_NUMBER_PATTERN, phone_number):
        raise ValidationPhoneNumberError("Неверный номер пользователя")

    email = user_info[5]
    if not re.fullmatch(EMAIL_PATTERN, email):
        raise ValidationEmailError("Неверный Email!")

    user = User(*user_info)
    return user

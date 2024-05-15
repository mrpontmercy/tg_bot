import logging
import re


logger = logging.getLogger(__name__)

phone_number_pattern = r"^[8][0-9]{10}$"  # Для российских номеров
name_s_name_patternt = r"^[a-zA-Zа-яА-Я]{3,}$"
email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class ValidationUserError(Exception):
    """Возникает когда не верно ввели данные для регистрации"""

    ...


class ValidationFirstNameError(Exception):
    """Возникает когда не верно ввели имя для регистрации"""

    ...


class ValidationSecondNameError(Exception):
    """Возникает когда не верно фамилию для регистрации"""

    ...


class ValidationPhoneNumberError(Exception):
    """Возникает когда не верно номер телефона для регистрации"""

    ...


class ValidationEmailError(Exception):
    """Возникает когда не верно ввели email для регистрации"""

    ...


def validate_user(user_info: list[str]):
    if len(user_info) != 4:
        raise ValidationUserError
    f_name = user_info[0]
    if not re.fullmatch(name_s_name_patternt, f_name):
        raise ValidationFirstNameError("Неверное имя пользователя")

    s_name = user_info[1]
    if not re.fullmatch(name_s_name_patternt, s_name):
        raise ValidationSecondNameError("Неверная фамилия пользователя")

    phone_number = user_info[2]
    if not re.fullmatch(phone_number_pattern, phone_number):
        print(phone_number)
        raise ValidationPhoneNumberError("Неверный номер пользователя")

    email = user_info[3]
    if not re.fullmatch(email_pattern, email):
        raise ValidationEmailError("Неверный Email!")

    return user_info

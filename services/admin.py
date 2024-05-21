import re
from db import fetch_all
from services.db import execute_delete, execute_update
from services.exceptions import InputMessageError, SubscriptionError
from services.utils import PHONE_NUMBER_PATTERN, Subscription


async def delete_subscription(sub_id: int):
    await execute_delete("subscription", "id=:sub_id", {"sub_id": sub_id})


async def update_user_to_lecturer(user_id):
    await execute_update(
        "user",
        "status=:status",
        "id=:user_id",
        {
            "status": "Преподаватель",
            "user_id": user_id,
        },
    )


def validate_phone_number(message: str):
    message = message.split(" ")
    if len(message) != 1:
        raise InputMessageError("Количество слов в сообщение должно быть равным 1")

    if not re.fullmatch(PHONE_NUMBER_PATTERN, message[0]):
        raise InputMessageError(
            "Сообщение должно содержать номер телефона. Начинается с 8. Всего 11 цифр"
        )

    return message[0]


def validate_num_of_classes(message: str):
    message = message.split(" ")
    if len(message) != 1:
        raise InputMessageError("Количество слов в сообщение должно быть равным 1")

    if not re.fullmatch("\d+", message[0]):
        raise InputMessageError("Сообщение должно содержать только цифры")

    return message[0]


async def get_all_subs():
    r_sql = """SELECT * FROM subscription"""

    subs = await fetch_all(r_sql)
    if not subs:
        raise SubscriptionError("Не удалось найти абонементы!")

    result = []
    for sub in subs:
        result.append(Subscription(**sub))

    return result


async def get_available_subs() -> list[Subscription]:
    r_sql = """SELECT * FROM subscription WHERE user_id IS NULL"""

    subs = await fetch_all(r_sql)
    if not subs:
        raise SubscriptionError("Не удалось найти доступные абонементы!")
    result = []
    for sub in subs:
        result.append(Subscription(**sub))

    return result

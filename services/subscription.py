import logging
from sqlite3 import Error

from db import get_db
from services.db import (
    fetch_one_subscription_where_cond,
    execute_delete,
    execute_update,
)
from services.exceptions import (
    InputMessageError,
    InvalidSubKey,
)
from services.utils import Subscription, UserID


def validate_args(args: list[str] | None):
    if args is not None and len(args) != 1:
        raise InputMessageError(
            "Нужно ввести только ключ абонимента!.\nПопробуйте снова."
        )

    return args


async def _get_sub_from_key(sub_key: str):
    curr_key_sub: Subscription | None = await fetch_one_subscription_where_cond(
        "sub_key=:sub_key",
        {"sub_key": sub_key},
    )
    if curr_key_sub is None:
        raise InvalidSubKey("Данный ключ невалиден. Обратитесь за другим ключом.")
    elif curr_key_sub.user_id is not None:
        raise InvalidSubKey(
            "Данный ключ уже зарегестрирован.\nОбратитесь за другим ключом."
        )

    return curr_key_sub


async def activate_key(sub_key: str, user: UserID):
    try:
        curr_key_sub = await _get_sub_from_key(sub_key)
    except InvalidSubKey:
        raise

    sub_by_user = await fetch_one_subscription_where_cond(
        "user_id=:user_id", {"user_id": user.id}
    )
    if sub_by_user is not None:
        num_of_classes_left = sub_by_user.num_of_classes
        result_num_of_classes = num_of_classes_left + curr_key_sub.num_of_classes
        try:
            await execute_delete(
                "subscription",
                "user_id=:user_id",
                {"user_id": user.id},
                autocommit=False,
            )
            await execute_update(
                "subscription",
                "user_id=:user_id, num_of_classes=:num_of_classes",
                "sub_key=:sub_key",
                {
                    "num_of_classes": result_num_of_classes,
                    "user_id": user.id,
                    "sub_key": curr_key_sub.sub_key,
                },
                autocommit=False,
            )
        except Error as e:
            await (await get_db()).rollback()
            raise
        await (await get_db()).commit()
        return "Ваш абонимент обновлен"
    try:
        await execute_update(
            "subscription",
            "user_id=:user_id, num_of_classes=:num_of_classes",
            "sub_key=:sub_key",
            {
                "num_of_classes": curr_key_sub.num_of_classes,
                "user_id": user.id,
                "sub_key": curr_key_sub.sub_key,
            },
        )
    except Error as e:
        raise
    return "Ваш абонимент активирован"

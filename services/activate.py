from telegram import Update
from telegram.ext import ContextTypes

from db import execute, fetch_one
from services.db import (
    execute_delete,
    execute_update,
    fetch_one_subscription_where_cond,
    fetch_one_user,
    fetch_one_user_with_sub,
)
from services.exceptions import (
    ErrorContextArgs,
    InvalidSubKey,
    UserError,
    SubscriptionError,
)
from services.utils import Subscription, UserID


async def activate_key_command(
    args: list[str] | None,
    telegram_id: int,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    - Проверяем валидность args
    - Узнаем зарегестрирован ли пользователь
    - Узнаем есть ли ключ в бд
    - Узнаем не занят ли ключ
    Активируем пользователю подписку (Если подписка уже есть, то продлеваем количество дней, старый ключ удаляем)
    """
    if args is not None and len(args) != 0:
        raise ErrorContextArgs("Введен неверный ключ!")

    user = await fetch_one_user({"telegram_id": telegram_id})

    if user is None:
        raise UserError("Пользователь не зарегестрирован!")

    sub_key: str = args[0]
    await activate_key(sub_key, user)
    return await update.effective_message.reply_text("Подписка успешно обновлена!")


def validate_args(args: list[str] | None):
    if args is not None and len(args) != 1:
        raise ErrorContextArgs

    return args


async def get_user(telegram_id: int):
    user = await fetch_one_user({"telegram_id": telegram_id})

    if user is None:
        raise UserError("Пользователь не зарегестрирован!")

    return user


async def _get_sub_from_key(sub_key: str):
    curr_key_sub: Subscription | None = await fetch_one_subscription_where_cond(
        "sub_key",
        ":sub_key",
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
    curr_key_sub = await _get_sub_from_key(sub_key)

    sub_by_user = await fetch_one_subscription_where_cond(
        "user_id", ":user_id", {"user_id": user.id}
    )
    if sub_by_user is not None:
        num_of_classes_left = sub_by_user.num_of_classes
        result_num_of_classes = num_of_classes_left + curr_key_sub.num_of_classes
        await execute_delete(
            "subscription",
            "user_id",
            ":user_id",
            {"user_id": user.id},
            autocommit=False,
        )
        await execute_update(
            "subscription",
            "user_id=:user_id, num_of_classes=:num_of_classes",
            "sub_key",
            ":sub_key",
            {
                "num_of_classes": result_num_of_classes,
                "user_id": user.id,
                "sub_key": curr_key_sub.sub_key,
            },
            autocommit=True,
        )
        return "Ваш абонимент обновлен"
    await execute_update(
        "subscription",
        "user_id=:user_id, num_of_classes=:num_of_classes",
        "sub_key",
        ":sub_key",
        {
            "num_of_classes": curr_key_sub.num_of_classes,
            "user_id": user.id,
            "sub_key": curr_key_sub.sub_key,
        },
    )
    return "Ваш абонимент активирован"

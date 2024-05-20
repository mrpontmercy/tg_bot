from services.db import execute_update


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

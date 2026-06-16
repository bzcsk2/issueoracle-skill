from sqlalchemy.ext.asyncio import AsyncSession


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return result.scalar_one_or_none()

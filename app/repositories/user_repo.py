"""User persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_models import User


async def get_user_by_google_id(session: AsyncSession, google_id: str) -> User | None:
    r = await session.execute(select(User).where(User.google_id == google_id))
    return r.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    google_id: str,
    email: str,
    name: str,
    picture: str | None,
) -> User:
    user = User(google_id=google_id, email=email, name=name, picture=picture)
    session.add(user)
    await session.flush()
    return user


async def get_or_create_user(
    session: AsyncSession,
    *,
    google_id: str,
    email: str,
    name: str,
    picture: str | None,
) -> User:
    user = await get_user_by_google_id(session, google_id)
    if user:
        user.name = name
        user.picture = picture
        await session.flush()
        return user
    return await create_user(session, google_id=google_id, email=email, name=name, picture=picture)

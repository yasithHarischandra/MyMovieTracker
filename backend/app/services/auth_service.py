from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import verify_password, create_access_token


async def authenticate_user(username: str, password: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == username.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def issue_token(user: User) -> str:
    return create_access_token({"sub": str(user.id), "username": user.username})

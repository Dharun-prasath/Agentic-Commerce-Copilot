"""Auth service — register, login, JWT."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import UserRegister, UserLogin, UserOut, TokenOut


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserRegister) -> TokenOut:
        # Check email uniqueness
        existing = await self.db.execute(select(User).where(User.email == data.email.lower()))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )
        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            name=data.name,
            phone=data.phone,
        )
        self.db.add(user)
        await self.db.flush()  # get the id
        await self.db.refresh(user)
        token = create_access_token({"sub": user.id})
        return TokenOut(access_token=token, user=UserOut.model_validate(user))

    async def login(self, data: UserLogin) -> TokenOut:
        result = await self.db.execute(select(User).where(User.email == data.email.lower()))
        user = result.scalar_one_or_none()
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )
        token = create_access_token({"sub": user.id})
        return TokenOut(access_token=token, user=UserOut.model_validate(user))

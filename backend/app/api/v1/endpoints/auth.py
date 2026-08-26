"""Auth API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.schemas.auth import UserRegister, UserLogin, TokenOut, UserOut
from app.services.auth_service import AuthService
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new customer account."""
    return await AuthService(db).register(data)


@router.post("/login", response_model=TokenOut)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive a JWT token."""
    return await AuthService(db).login(data)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    """Get the current authenticated user."""
    return UserOut.model_validate(user)

"""Wishlist API endpoints (authenticated only)."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.schemas.commerce import WishlistItemAdd, WishlistOut
from app.services.wishlist_address_service import WishlistService
from app.models.models import User

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=WishlistOut)
async def get_wishlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WishlistService(db).get_wishlist(user.id)


@router.post("/items", response_model=WishlistOut, status_code=201)
async def add_to_wishlist(
    data: WishlistItemAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WishlistService(db).add_item(user.id, data)


@router.delete("/items/{product_id}", response_model=WishlistOut)
async def remove_from_wishlist(
    product_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WishlistService(db).remove_item(user.id, product_id)

"""Wishlist and Address services."""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.models import Wishlist, WishlistItem, Product, Address
from app.schemas.commerce import (
    WishlistOut, WishlistItemOut, WishlistItemAdd,
    AddressCreate, AddressUpdate, AddressOut
)


class WishlistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_wishlist(self, user_id: str) -> Wishlist:
        result = await self.db.execute(
            select(Wishlist).options(selectinload(Wishlist.items).selectinload(WishlistItem.product).selectinload(Product.images))
            .where(Wishlist.user_id == user_id)
        )
        wishlist = result.scalar_one_or_none()
        if not wishlist:
            wishlist = Wishlist(user_id=user_id, items=[])
            self.db.add(wishlist)
            await self.db.flush()
        return wishlist

    async def get_wishlist(self, user_id: str) -> WishlistOut:
        wishlist = await self.get_or_create_wishlist(user_id)
        return self._serialize(wishlist)

    async def add_item(self, user_id: str, data: WishlistItemAdd) -> WishlistOut:
        wishlist = await self.get_or_create_wishlist(user_id)
        # Check product exists
        prod = await self.db.execute(select(Product).where(Product.id == data.product_id))
        product = prod.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        existing = await self.db.execute(
            select(WishlistItem).where(
                WishlistItem.wishlist_id == wishlist.id,
                WishlistItem.product_id == data.product_id,
            )
        )
        if not existing.scalar_one_or_none():
            self.db.add(WishlistItem(wishlist_id=wishlist.id, product_id=data.product_id))
            await self.db.flush()
        return await self.get_wishlist(user_id)

    async def remove_item(self, user_id: str, product_id: str) -> WishlistOut:
        wishlist = await self.get_or_create_wishlist(user_id)
        result = await self.db.execute(
            select(WishlistItem).where(
                WishlistItem.wishlist_id == wishlist.id,
                WishlistItem.product_id == product_id,
            )
        )
        item = result.scalar_one_or_none()
        if item:
            await self.db.delete(item)
            await self.db.flush()
        return await self.get_wishlist(user_id)

    def _serialize(self, wishlist: Wishlist) -> WishlistOut:
        items = []
        for wi in (wishlist.items or []):
            p = wi.product
            if p:
                thumbnail = p.thumbnail or (p.images[0].url if getattr(p, "images", None) else None)
                items.append(WishlistItemOut(
                    id=wi.id, product_id=p.id, product_name=p.name,
                    product_brand=p.brand, product_thumbnail=thumbnail,
                    product_slug=p.slug, price=p.price,
                    original_price=p.original_price,
                    discount_percentage=p.discount_percentage,
                    rating=p.rating, stock=p.stock,
                ))
        return WishlistOut(id=wishlist.id, items=items, item_count=len(items))


class AddressService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_addresses(self, user_id: str) -> List[AddressOut]:
        result = await self.db.execute(
            select(Address).where(Address.user_id == user_id).order_by(Address.is_default.desc())
        )
        return [AddressOut.model_validate(a) for a in result.scalars()]

    async def create_address(self, user_id: str, data: AddressCreate) -> AddressOut:
        if data.is_default:
            await self._clear_defaults(user_id)
        address = Address(user_id=user_id, **data.model_dump())
        self.db.add(address)
        await self.db.flush()
        await self.db.refresh(address)
        return AddressOut.model_validate(address)

    async def update_address(self, user_id: str, address_id: str, data: AddressUpdate) -> AddressOut:
        address = await self._get(user_id, address_id)
        if data.is_default:
            await self._clear_defaults(user_id)
        for field, value in data.model_dump().items():
            setattr(address, field, value)
        await self.db.flush()
        return AddressOut.model_validate(address)

    async def delete_address(self, user_id: str, address_id: str) -> None:
        address = await self._get(user_id, address_id)
        await self.db.delete(address)

    async def _get(self, user_id: str, address_id: str) -> Address:
        result = await self.db.execute(
            select(Address).where(Address.id == address_id, Address.user_id == user_id)
        )
        address = result.scalar_one_or_none()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        return address

    async def _clear_defaults(self, user_id: str) -> None:
        result = await self.db.execute(
            select(Address).where(Address.user_id == user_id, Address.is_default == True)
        )
        for addr in result.scalars():
            addr.is_default = False

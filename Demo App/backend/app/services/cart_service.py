"""Cart service — full CRUD with stock validation."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.models import Cart, CartItem, Product, User
from app.schemas.commerce import CartItemAdd, CartItemUpdate, CartOut, CartItemOut


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_cart(self, user: Optional[User], session_id: Optional[str]) -> Cart:
        """Get existing cart or create one. Auth users get user-linked cart."""
        if user:
            result = await self.db.execute(
                select(Cart).options(selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images))
                .where(Cart.user_id == user.id)
            )
            cart = result.scalar_one_or_none()
            if not cart:
                cart = Cart(user_id=user.id, session_id=session_id)
                self.db.add(cart)
                await self.db.flush()
        else:
            if not session_id:
                raise HTTPException(status_code=400, detail="session_id required for anonymous cart")
            result = await self.db.execute(
                select(Cart).options(selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images))
                .where(Cart.session_id == session_id, Cart.user_id == None)
            )
            cart = result.scalar_one_or_none()
            if not cart:
                cart = Cart(session_id=session_id)
                self.db.add(cart)
                await self.db.flush()
        return cart

    async def get_cart(self, user: Optional[User], session_id: Optional[str]) -> CartOut:
        cart = await self._load_cart(user, session_id)
        if not cart:
            return CartOut(id="", items=[], coupon_code=None, item_count=0, subtotal=0.0)
        return self._serialize(cart)

    async def add_item(
        self, user: Optional[User], session_id: Optional[str], data: CartItemAdd
    ) -> CartOut:
        cart = await self.get_or_create_cart(user, session_id)
        # Load product
        product = await self._get_product(data.product_id)
        if product.stock < 1:
            raise HTTPException(status_code=400, detail="Product is out of stock")

        # Check if item already in cart
        existing = await self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == data.product_id)
        )
        item = existing.scalar_one_or_none()
        if item:
            new_qty = item.quantity + data.quantity
            if new_qty > product.stock:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot add more. Only {product.stock} units available.",
                )
            item.quantity = new_qty
        else:
            if data.quantity > product.stock:
                raise HTTPException(
                    status_code=400,
                    detail=f"Only {product.stock} units available.",
                )
            item = CartItem(cart_id=cart.id, product_id=data.product_id, quantity=data.quantity)
            self.db.add(item)

        await self.db.flush()
        return await self.get_cart(user, session_id)

    async def update_item(
        self, user: Optional[User], session_id: Optional[str], item_id: str, data: CartItemUpdate
    ) -> CartOut:
        cart = await self._load_cart(user, session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        item = await self._get_cart_item(cart.id, item_id)
        product = await self._get_product(item.product_id)
        if data.quantity > product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Only {product.stock} units available.",
            )
        item.quantity = data.quantity
        await self.db.flush()
        return await self.get_cart(user, session_id)

    async def remove_item(
        self, user: Optional[User], session_id: Optional[str], item_id: str
    ) -> CartOut:
        cart = await self._load_cart(user, session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        item = await self._get_cart_item(cart.id, item_id)
        await self.db.delete(item)
        await self.db.flush()
        return await self.get_cart(user, session_id)

    async def clear_cart(self, user: Optional[User], session_id: Optional[str]) -> None:
        cart = await self._load_cart(user, session_id)
        if cart:
            for item in cart.items:
                await self.db.delete(item)
            await self.db.flush()

    async def apply_coupon(
        self, user: Optional[User], session_id: Optional[str], coupon_code: Optional[str]
    ) -> CartOut:
        cart = await self._load_cart(user, session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        cart.coupon_code = coupon_code
        await self.db.flush()
        return await self.get_cart(user, session_id)

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _load_cart(self, user: Optional[User], session_id: Optional[str]) -> Optional[Cart]:
        if user:
            result = await self.db.execute(
                select(Cart).options(selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images))
                .where(Cart.user_id == user.id)
                .execution_options(populate_existing=True)
            )
        elif session_id:
            result = await self.db.execute(
                select(Cart).options(selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images))
                .where(Cart.session_id == session_id, Cart.user_id == None)
                .execution_options(populate_existing=True)
            )
        else:
            return None
        return result.scalar_one_or_none()

    async def _get_product(self, product_id: str) -> Product:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    async def _get_cart_item(self, cart_id: str, item_id: str) -> CartItem:
        result = await self.db.execute(
            select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        return item

    def _serialize(self, cart: Cart) -> CartOut:
        items = []
        subtotal = 0.0
        for ci in (cart.items or []):
            p = ci.product
            if not p:
                continue
            sub = p.price * ci.quantity
            subtotal += sub
            thumbnail = p.thumbnail
            if not thumbnail and p.images:
                thumbnail = p.images[0].url if p.images else None
            items.append(CartItemOut(
                id=ci.id,
                product_id=p.id,
                product_name=p.name,
                product_brand=p.brand,
                product_thumbnail=thumbnail,
                product_slug=p.slug,
                unit_price=p.price,
                original_price=p.original_price,
                quantity=ci.quantity,
                subtotal=sub,
                stock=p.stock,
            ))
        return CartOut(
            id=cart.id,
            items=items,
            coupon_code=cart.coupon_code,
            item_count=sum(i.quantity for i in items),
            subtotal=round(subtotal, 2),
        )

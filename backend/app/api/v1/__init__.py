"""API v1 router — aggregates all endpoint routers."""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, products, cart, wishlist, events
from app.api.v1.endpoints.commerce import (
    addresses_router, checkout_router, payments_router, orders_router
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(wishlist.router)
api_router.include_router(events.router)
api_router.include_router(addresses_router)
api_router.include_router(checkout_router)
api_router.include_router(payments_router)
api_router.include_router(orders_router)

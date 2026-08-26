"""Products API endpoints."""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.products import ProductListResponse, ProductDetail, SearchSuggestion
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None, description="Category slug"),
    brand: Optional[str] = Query(None, description="Brand name(s), comma-separated"),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    sort_by: str = Query("popularity", enum=["price_asc","price_desc","rating","newest","discount","popularity"]),
    is_featured: Optional[bool] = Query(None),
    is_trending: Optional[bool] = Query(None),
    is_best_seller: Optional[bool] = Query(None),
    ram: Optional[str] = Query(None),
    storage: Optional[str] = Query(None),
    processor: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List and search products with full filter/sort support."""
    return await ProductService(db).list_products(
        page=page, page_size=page_size, search=search,
        category_slug=category, brand=brand,
        min_price=min_price, max_price=max_price, min_rating=min_rating,
        sort_by=sort_by,
        is_featured=is_featured, is_trending=is_trending, is_best_seller=is_best_seller,
        ram=ram, storage=storage, processor=processor,
    )


@router.get("/search/suggestions", response_model=SearchSuggestion)
async def search_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """Return search suggestions for autocomplete (debounce on frontend)."""
    return await ProductService(db).get_search_suggestions(q, limit)


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all product categories."""
    return await ProductService(db).get_categories()


@router.get("/brands")
async def list_brands(db: AsyncSession = Depends(get_db)):
    """List all distinct brands."""
    return await ProductService(db).get_brands()


@router.get("/{id_or_slug}", response_model=ProductDetail)
async def get_product(id_or_slug: str, db: AsyncSession = Depends(get_db)):
    """Get full product detail by ID or slug."""
    return await ProductService(db).get_product(id_or_slug)

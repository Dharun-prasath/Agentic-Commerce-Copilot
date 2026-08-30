"""Product service — catalog, search, filtering, sorting."""
from typing import Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, cast, String
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import math

from app.models.models import Product, Category, ProductReview, ProductCompatibility
from app.schemas.products import (
    ProductSummary, ProductDetail, ProductListResponse,
    SearchSuggestion, ReviewOut
)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category_slug: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        sort_by: str = "popularity",  # price_asc, price_desc, rating, newest, discount
        is_featured: Optional[bool] = None,
        is_trending: Optional[bool] = None,
        is_best_seller: Optional[bool] = None,
        # Spec filters
        ram: Optional[str] = None,
        storage: Optional[str] = None,
        processor: Optional[str] = None,
    ) -> ProductListResponse:
        query = (
            select(Product)
            .options(selectinload(Product.category), selectinload(Product.images))
            .where(Product.is_active == True)
        )

        # ── Search ──────────────────────────────────────────────────────────
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(Product.name).like(search_term),
                    func.lower(Product.brand).like(search_term),
                    func.lower(Product.description).like(search_term),
                    func.cast(Product.tags, String).like(search_term),
                )
            )

        # ── Category ─────────────────────────────────────────────────────────
        if category_slug:
            cat_result = await self.db.execute(
                select(Category).where(Category.slug == category_slug)
            )
            cat = cat_result.scalar_one_or_none()
            if cat:
                query = query.where(Product.category_id == cat.id)

        # ── Brand ─────────────────────────────────────────────────────────────
        if brand:
            brands = [b.strip() for b in brand.split(",")]
            query = query.where(Product.brand.in_(brands))

        # ── Price ─────────────────────────────────────────────────────────────
        if min_price is not None:
            query = query.where(Product.price >= min_price)
        if max_price is not None:
            query = query.where(Product.price <= max_price)

        # ── Rating ────────────────────────────────────────────────────────────
        if min_rating is not None:
            query = query.where(Product.rating >= min_rating)

        # ── Flags ─────────────────────────────────────────────────────────────
        if is_featured is not None:
            query = query.where(Product.is_featured == is_featured)
        if is_trending is not None:
            query = query.where(Product.is_trending == is_trending)
        if is_best_seller is not None:
            query = query.where(Product.is_best_seller == is_best_seller)

        # ── Spec Filters ──────────────────────────────────────────────────────
        if ram:
            rams = [r.strip() for r in ram.split(",")]
            query = query.where(
                or_(*[func.cast(Product.specifications, String).like(f"%{r}%") for r in rams])
            )
        if storage:
            storages = [s.strip() for s in storage.split(",")]
            query = query.where(
                or_(*[func.cast(Product.specifications, String).like(f"%{s}%") for s in storages])
            )
        if processor:
            procs = [p.strip().lower() for p in processor.split(",")]
            query = query.where(
                or_(*[func.lower(func.cast(Product.specifications, String)).like(f"%{p}%") for p in procs])
            )

        # ── Sort ─────────────────────────────────────────────────────────────
        sort_map = {
            "price_asc": Product.price.asc(),
            "price_desc": Product.price.desc(),
            "rating": Product.rating.desc(),
            "newest": Product.created_at.desc(),
            "discount": Product.discount_percentage.desc(),
            "popularity": Product.review_count.desc(),
        }
        query = query.order_by(sort_map.get(sort_by, Product.review_count.desc()))

        # ── Count ─────────────────────────────────────────────────────────────
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # ── Paginate ──────────────────────────────────────────────────────────
        offset = (page - 1) * page_size
        result = await self.db.execute(query.offset(offset).limit(page_size))
        products = result.scalars().all()

        items = [self._to_summary(p) for p in products]
        return ProductListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )

    async def get_product(self, id_or_slug: str) -> ProductDetail:
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.reviews),
                selectinload(Product.accessories).selectinload(ProductCompatibility.target_product).selectinload(Product.images),
                selectinload(Product.accessories).selectinload(ProductCompatibility.target_product).selectinload(Product.category),
            )
            .where(
                or_(Product.id == id_or_slug, Product.slug == id_or_slug),
                Product.is_active == True,
            )
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return self._to_detail(product)

    async def get_search_suggestions(self, q: str, limit: int = 5) -> SearchSuggestion:
        if len(q) < 1:
            return SearchSuggestion(query=q, products=[], brands=[], categories=[])
        term = f"%{q.lower()}%"
        # Use explicit column selects to avoid any lazy-loading in async context
        from sqlalchemy import text
        result = await self.db.execute(
            select(
                Product.id,
                Product.name,
                Product.slug,
                Product.brand,
                Product.category_id,
                Product.price,
                Product.original_price,
                Product.discount_percentage,
                Product.currency,
                Product.thumbnail,
                Product.rating,
                Product.review_count,
                Product.stock,
                Product.is_featured,
                Product.is_trending,
                Product.is_best_seller,
                Product.tags,
            )
            .where(
                Product.is_active == True,
                or_(
                    func.lower(Product.name).like(term),
                    func.lower(Product.brand).like(term),
                ),
            )
            .limit(limit)
        )
        rows = result.mappings().all()
        brands = list({r["brand"] for r in rows})[:5]
        suggestion_products = [
            ProductSummary(
                id=r["id"],
                name=r["name"],
                slug=r["slug"],
                brand=r["brand"],
                category_id=r["category_id"],
                category=None,
                price=r["price"],
                original_price=r["original_price"],
                discount_percentage=r["discount_percentage"],
                currency=r["currency"],
                thumbnail=r["thumbnail"],
                rating=r["rating"],
                review_count=r["review_count"],
                stock=r["stock"],
                is_featured=r["is_featured"],
                is_trending=r["is_trending"],
                is_best_seller=r["is_best_seller"],
                tags=r["tags"] or [],
            )
            for r in rows
        ]
        return SearchSuggestion(
            query=q,
            products=suggestion_products,
            brands=brands,
            categories=[],
        )

    async def get_categories(self) -> List[dict]:
        result = await self.db.execute(select(Category).order_by(Category.name))
        return [{"id": c.id, "name": c.name, "slug": c.slug, "icon": c.icon} for c in result.scalars()]

    async def get_brands(self) -> List[str]:
        result = await self.db.execute(
            select(Product.brand).distinct().where(Product.is_active == True).order_by(Product.brand)
        )
        return [r[0] for r in result.all()]

    def _to_summary(self, p: Product) -> ProductSummary:
        thumbnail = p.thumbnail
        if not thumbnail and p.images:
            primary = next((i for i in p.images if i.is_primary), p.images[0] if p.images else None)
            thumbnail = primary.url if primary else None
        return ProductSummary(
            id=p.id,
            name=p.name,
            slug=p.slug,
            brand=p.brand,
            category_id=p.category_id,
            category=p.category,
            price=p.price,
            original_price=p.original_price,
            discount_percentage=p.discount_percentage,
            currency=p.currency,
            thumbnail=thumbnail,
            rating=p.rating,
            review_count=p.review_count,
            stock=p.stock,
            is_featured=p.is_featured,
            is_trending=p.is_trending,
            is_best_seller=p.is_best_seller,
            tags=p.tags or [],
        )

    def _to_detail(self, p: Product) -> ProductDetail:
        summary = self._to_summary(p)
        reviews = []
        for r in (p.reviews or []):
            reviews.append(ReviewOut(
                id=r.id,
                reviewer_name=r.reviewer_name,
                rating=r.rating,
                title=r.title,
                body=r.body,
                is_verified_purchase=r.is_verified_purchase,
                helpful_count=r.helpful_count,
                created_at=r.created_at.isoformat() if r.created_at else "",
            ))
            
        accessories = []
        for acc in getattr(p, "accessories", []):
            if acc.target_product:
                accessories.append({
                    "compatibility_type": acc.compatibility_type.value,
                    "target_product": self._to_summary(acc.target_product).model_dump()
                })

        return ProductDetail(
            **summary.model_dump(),
            description=p.description,
            specifications=p.specifications or {},
            features=p.features or [],
            images=[
                {"id": i.id, "url": i.url, "alt_text": i.alt_text, "is_primary": i.is_primary, "sort_order": i.sort_order}
                for i in sorted(p.images or [], key=lambda x: x.sort_order)
            ],
            reviews=reviews,
            accessories=accessories,
        )

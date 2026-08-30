"""Pydantic schemas — Products, Categories, Reviews"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


import enum

class CompatibilityType(str, enum.Enum):
    COMPATIBLE = "COMPATIBLE"
    RECOMMENDED = "RECOMMENDED"
    UNIVERSAL = "UNIVERSAL"
    SIZE_MATCH = "SIZE_MATCH"
    REQUIRED_ADAPTER = "REQUIRED_ADAPTER"

class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductImageOut(BaseModel):
    id: str
    url: str
    alt_text: Optional[str] = None
    is_primary: bool
    sort_order: int

    model_config = {"from_attributes": True}


class ReviewOut(BaseModel):
    id: str
    reviewer_name: str
    rating: int
    title: Optional[str] = None
    body: str
    is_verified_purchase: bool
    helpful_count: int
    created_at: str

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: Any) -> None:
        if hasattr(self, 'created_at') and self.created_at and not isinstance(self.created_at, str):
            object.__setattr__(self, 'created_at', self.created_at.isoformat())

class AccessoryOut(BaseModel):
    compatibility_type: CompatibilityType
    target_product: 'ProductSummary'

    model_config = {"from_attributes": True}

class ProductSummary(BaseModel):
    """Lightweight product card for listing pages."""
    id: str
    name: str
    slug: str
    brand: str
    category_id: str
    category: Optional[CategoryOut] = None
    price: float
    original_price: float
    discount_percentage: float
    currency: str
    thumbnail: Optional[str] = None
    rating: float
    review_count: int
    stock: int
    is_featured: bool
    is_trending: bool
    is_best_seller: bool
    tags: List[str] = []

    model_config = {"from_attributes": True}


class ProductDetail(ProductSummary):
    """Full product detail including specs, features, images, reviews."""
    description: str
    specifications: Dict[str, Any] = {}
    features: List[str] = []
    images: List[ProductImageOut] = []
    reviews: List[ReviewOut] = []
    accessories: List[AccessoryOut] = []

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: List[ProductSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class SearchSuggestion(BaseModel):
    query: str
    products: List[ProductSummary]
    brands: List[str]
    categories: List[str]


class ReviewCreate(BaseModel):
    rating: int
    title: Optional[str] = None
    body: str

    @classmethod
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v

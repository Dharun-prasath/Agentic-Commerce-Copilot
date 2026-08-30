"""
All SQLAlchemy ORM models for the Agentic Commerce e-commerce platform.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, JSON, Enum as SAEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class CouponType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FLAT = "FLAT"


class CompatibilityType(str, enum.Enum):
    COMPATIBLE = "COMPATIBLE"
    RECOMMENDED = "RECOMMENDED"
    UNIVERSAL = "UNIVERSAL"
    SIZE_MATCH = "SIZE_MATCH"
    REQUIRED_ADAPTER = "REQUIRED_ADAPTER"


class EventType(str, enum.Enum):
    PRODUCT_SEARCHED = "PRODUCT_SEARCHED"
    PRODUCT_VIEWED = "PRODUCT_VIEWED"
    PRODUCT_DETAILS_VIEWED = "PRODUCT_DETAILS_VIEWED"
    PRODUCT_IMAGE_VIEWED = "PRODUCT_IMAGE_VIEWED"
    PRODUCT_SPECIFICATIONS_VIEWED = "PRODUCT_SPECIFICATIONS_VIEWED"
    PRODUCT_REVIEW_VIEWED = "PRODUCT_REVIEW_VIEWED"
    PRODUCT_COMPARED = "PRODUCT_COMPARED"
    WISHLIST_ADDED = "WISHLIST_ADDED"
    WISHLIST_REMOVED = "WISHLIST_REMOVED"
    CART_ITEM_ADDED = "CART_ITEM_ADDED"
    CART_ITEM_REMOVED = "CART_ITEM_REMOVED"
    CART_UPDATED = "CART_UPDATED"
    CHECKOUT_STARTED = "CHECKOUT_STARTED"
    CHECKOUT_COMPLETED = "CHECKOUT_COMPLETED"
    PAYMENT_STARTED = "PAYMENT_STARTED"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    ORDER_CREATED = "ORDER_CREATED"


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    cart = relationship("Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")
    wishlist = relationship("Wishlist", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    reviews = relationship("ProductReview", back_populates="user")


# ─────────────────────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=new_uuid)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(255), nullable=True)
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    parent = relationship("Category", remote_side="Category.id")
    children = relationship("Category", back_populates="parent")
    models = relationship("ProductModel", back_populates="category")


# ─────────────────────────────────────────────────────────────────────────────
# Brand -> Series -> ProductModel -> Product (SKU)
# ─────────────────────────────────────────────────────────────────────────────

class Brand(Base):
    __tablename__ = "brands"

    id = Column(String, primary_key=True, default=new_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    series = relationship("Series", back_populates="brand", cascade="all, delete-orphan")


class Series(Base):
    __tablename__ = "series"

    id = Column(String, primary_key=True, default=new_uuid)
    brand_id = Column(String, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    brand = relationship("Brand", back_populates="series")
    models = relationship("ProductModel", back_populates="series", cascade="all, delete-orphan")


class ProductModel(Base):
    __tablename__ = "product_models"

    id = Column(String, primary_key=True, default=new_uuid)
    series_id = Column(String, ForeignKey("series.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    series = relationship("Series", back_populates="models")
    category = relationship("Category", back_populates="models")
    products = relationship("Product", back_populates="model", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# Product
# ─────────────────────────────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=new_uuid)
    product_model_id = Column(String, ForeignKey("product_models.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    # Keeping category_id and brand for backwards compatibility with existing frontend/queries,
    # even though they are technically denormalized from ProductModel -> Series -> Brand
    brand = Column(String(100), nullable=False, index=True)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)            # selling price (INR)
    original_price = Column(Float, nullable=False)  # MRP
    discount_percentage = Column(Float, default=0.0)
    currency = Column(String(10), default="INR")
    thumbnail = Column(String(500), nullable=True)
    specifications = Column(JSON, default=dict)    # {processor, ram, storage, ...}
    features = Column(JSON, default=list)          # ["Feature 1", ...]
    tags = Column(JSON, default=list)              # ["gaming", "laptop", ...]
    stock = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_trending = Column(Boolean, default=False)
    is_best_seller = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    model = relationship("ProductModel", back_populates="products")
    category = relationship("Category")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")
    wishlist_items = relationship("WishlistItem", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    accessories = relationship(
        "ProductCompatibility",
        foreign_keys="[ProductCompatibility.source_product_id]",
        back_populates="source_product",
        cascade="all, delete-orphan"
    )

class ProductCompatibility(Base):
    __tablename__ = "product_compatibilities"
    __table_args__ = (UniqueConstraint("source_product_id", "target_product_id"),)

    id = Column(String, primary_key=True, default=new_uuid)
    source_product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    target_product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    compatibility_type = Column(SAEnum(CompatibilityType), nullable=False, default=CompatibilityType.COMPATIBLE)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    source_product = relationship("Product", foreign_keys=[source_product_id], back_populates="accessories")
    target_product = relationship("Product", foreign_keys=[target_product_id])


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(String, primary_key=True, default=new_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(500), nullable=False)
    alt_text = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    product = relationship("Product", back_populates="images")


class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(String, primary_key=True, default=new_uuid)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_name = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    is_verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


# ─────────────────────────────────────────────────────────────────────────────
# Wishlist
# ─────────────────────────────────────────────────────────────────────────────

class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="wishlist")
    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (UniqueConstraint("wishlist_id", "product_id"),)

    id = Column(String, primary_key=True, default=new_uuid)
    wishlist_id = Column(String, ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    wishlist = relationship("Wishlist", back_populates="items")
    product = relationship("Product", back_populates="wishlist_items")


# ─────────────────────────────────────────────────────────────────────────────
# Cart
# ─────────────────────────────────────────────────────────────────────────────

class Cart(Base):
    __tablename__ = "carts"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True)
    session_id = Column(String(255), nullable=True, index=True)  # for anonymous carts
    coupon_code = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id"),)

    id = Column(String, primary_key=True, default=new_uuid)
    cart_id = Column(String, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")


# ─────────────────────────────────────────────────────────────────────────────
# Coupon
# ─────────────────────────────────────────────────────────────────────────────

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(String, primary_key=True, default=new_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(SAEnum(CouponType), nullable=False)
    value = Column(Float, nullable=False)           # percent (10.0) or flat (500)
    min_order_amount = Column(Float, default=0.0)   # minimum cart subtotal
    max_discount = Column(Float, nullable=True)     # cap for percentage coupons
    max_uses = Column(Integer, nullable=True)        # None = unlimited
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# Address
# ─────────────────────────────────────────────────────────────────────────────

class Address(Base):
    __tablename__ = "addresses"

    id = Column(String, primary_key=True, default=new_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    line1 = Column(String(255), nullable=False)
    line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), default="India")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="addresses")


# ─────────────────────────────────────────────────────────────────────────────
# Order
# ─────────────────────────────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=new_uuid)
    order_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = Column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING)

    # Address snapshot (denormalized so order is immutable after placement)
    shipping_name = Column(String(100), nullable=False)
    shipping_phone = Column(String(20), nullable=False)
    shipping_line1 = Column(String(255), nullable=False)
    shipping_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    shipping_country = Column(String(100), nullable=False)

    # Delivery
    delivery_method = Column(String(50), default="STANDARD")
    delivery_days = Column(Integer, default=5)

    # Pricing (all server-calculated)
    subtotal = Column(Float, nullable=False)
    coupon_code = Column(String(50), nullable=True)
    coupon_discount = Column(Float, default=0.0)
    tax_amount = Column(Float, nullable=False)
    shipping_charge = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=new_uuid)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_name = Column(String(255), nullable=False)   # snapshot
    product_brand = Column(String(100), nullable=False)  # snapshot
    product_thumbnail = Column(String(500), nullable=True)
    unit_price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# ─────────────────────────────────────────────────────────────────────────────
# Payment
# ─────────────────────────────────────────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=new_uuid)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    razorpay_order_id = Column(String(100), nullable=True, index=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    razorpay_signature = Column(String(500), nullable=True)
    amount = Column(Float, nullable=False)            # in INR
    amount_in_paise = Column(Integer, nullable=False) # Razorpay uses paise
    currency = Column(String(10), default="INR")
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING)
    failure_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    order = relationship("Order", back_populates="payment")


# ─────────────────────────────────────────────────────────────────────────────
# Event Tracking (Copilot-ready)
# ─────────────────────────────────────────────────────────────────────────────

class Event(Base):
    """
    Immutable event log for all customer behavioural events.
    Designed for consumption by the future Agentic Commerce Copilot.
    Append-only — never update or delete events.
    """
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_session_id", "session_id"),
        Index("ix_events_user_id", "user_id"),
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_created_at", "created_at"),
    )

    id = Column(String, primary_key=True, default=new_uuid)
    event_type = Column(SAEnum(EventType), nullable=False)
    session_id = Column(String(255), nullable=False)   # always present
    user_id = Column(String, nullable=True)             # null for anonymous
    product_id = Column(String, nullable=True)
    category_id = Column(String, nullable=True)
    order_id = Column(String, nullable=True)
    event_metadata = Column(JSON, default=dict)               # rich behavioural data
    created_at = Column(DateTime(timezone=True), default=utcnow)

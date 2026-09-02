# Demo App Database Structure

This document details the database structure and access patterns for the Demo App, strictly derived from the existing codebase.

## Overview

- **Database Technology:** PostgreSQL
- **Connection Method:** Async SQLAlchemy via `postgresql+asyncpg://`
- **ORM:** SQLAlchemy (DeclarativeBase)

---

## 1. Products

The `products` table stores core product information.

| Field | Type | Required | Purpose | Example |
|-------|------|----------|---------|---------|
| `id` | UUID (String) | Yes | Primary Key | `bb362054-...` |
| `name` | String(255) | Yes | Display Name | `XPS 16` |
| `slug` | String(255) | Yes | URL slug (indexed) | `dell-xps-16` |
| `brand` | String(100) | Yes | Brand name (indexed) | `Dell` |
| `category_id` | UUID (String)| Yes | FK to `categories` | `...` |
| `description` | Text | Yes | Detailed description | `...` |
| `stock` | Integer | Yes (def: 0)| Available inventory count| `100` |
| `is_active` | Boolean | Yes (def: True)| Soft-delete/visibility flag | `True` |

---

## 2. Product Specifications

Detailed technical specifications are stored directly on the `products` table in a `JSON` column, rather than in a separate attributes table.

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `specifications`| JSON | No (def: `{}`) | Key-value dictionary of specs (e.g., `{"processor": "Core Ultra 9", "ram": "64GB"}`) |
| `features` | JSON | No (def: `[]`) | Array of feature strings |

*Note on Specifications:* The Demo App API allows filtering by specific specifications (like `ram`, `storage`, and `processor`) by casting the JSON `specifications` column to a String and performing a `LIKE` SQL query (e.g., `func.cast(Product.specifications, String).like(f"%{r}%")`).

---

## 3. Product Images

Images are handled via a combination of a denormalized thumbnail and a dedicated `product_images` table for galleries.

**On `products` table:**
- `thumbnail` (String): A direct URL path (e.g., `/images/products/dell_xps.png`).

**In `product_images` table:**
- `id` (UUID)
- `product_id` (UUID, FK to `products.id`)
- `url` (String(500))
- `is_primary` (Boolean)
- `sort_order` (Integer)

---

## 4. Product Categories

Categories are hierarchical (parent-child relationship) and stored in the `categories` table.

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `id` | UUID (String) | Yes | Primary Key |
| `name` | String(100) | Yes | Category Name |
| `slug` | String(100) | Yes | URL Slug (indexed) |
| `parent_id`| UUID (String) | No | Self-referencing FK |

---

## 5. Product Pricing

Pricing data is stored directly on the `products` table.

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `price` | Float | Yes | Current selling price (INR) |
| `original_price`| Float | Yes | MRP / Original price |
| `discount_percentage`| Float | Yes (def: 0.0) | Calculated discount |
| `currency` | String(10)| Yes (def: INR) | Currency code |

---

## 6. Customers / Users

The Demo App uses a `users` table to represent customers.

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `id` | UUID (String) | Yes | Primary Key (Customer ID) |
| `email` | String(255) | Yes | Login email (unique, indexed) |
| `password_hash`| String(255) | Yes | Hashed password |
| `name` | String(255) | Yes | Full Name |
| `phone` | String(20) | No | Phone number |

---

## 7. Carts & Cart Items

Shopping carts are persisted in the database. Carts can be associated with an authenticated `user_id` or an anonymous `session_id`.

**`carts` Table:**
- `id` (UUID)
- `user_id` (UUID, FK to `users.id`, nullable, unique per user)
- `session_id` (String, indexed, for anonymous/guest carts)

**`cart_items` Table:**
- `id` (UUID)
- `cart_id` (UUID, FK to `carts.id`)
- `product_id` (UUID, FK to `products.id`)
- `quantity` (Integer, default: 1)

---

## Required Integrations (How-to Guide)

### A. Searching Products
**API Endpoint:** `GET /api/v1/products/search/suggestions`
**Purpose:** Autocomplete search.
**Flow:**
1. Client sends `GET /api/v1/products/search/suggestions?q={query}&limit={limit}`
2. Route calls `ProductService(db).get_search_suggestions()`
3. Performs `LIKE` query on `Product.name` and `Product.brand`.
4. Returns a `SearchSuggestion` JSON object containing a list of products.

*Alternatively, for full filtering, use `GET /api/v1/products`.*

### B. Identifying a Customer
**Method:** JWT Authentication.
The Demo App uses `Depends(get_current_user_optional)` in its routes. This dependency parses the `Authorization: Bearer <token>` header, decodes the JWT (using the shared `JWT_SECRET`), and extracts the `sub` claim (which holds the `user_id` UUID).

### C. Adding a Product to the Cart
**API Endpoint:** `POST /api/v1/cart/items`
**Payload:**
```json
{
  "product_id": "<UUID>",
  "quantity": 1
}
```
**Headers:**
To add it to a registered customer's cart, include:
`Authorization: Bearer <JWT Token>`
To add it to a guest cart, include:
`X-Session-Id: <Session String>`
**Flow:**
The `CartService.add_item()` method retrieves or creates the `Cart` for the user/session, verifies `product.stock >= 1`, and upserts the `CartItem`.

### D. Verifying the Cart
**API Endpoint:** `GET /api/v1/cart`
**Headers:** Pass `Authorization: Bearer <JWT Token>` (for customers) or `X-Session-Id` (for guests).
**Response:** Returns a `CartOut` schema containing an `items` array. You can verify the product is in the cart by checking if the `product_id` exists in this array.

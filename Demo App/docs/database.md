# Database Schema

The Demo Commerce Application utilizes PostgreSQL, managed by SQLAlchemy 2.0 ORM. All tables use UUIDs for primary keys to ensure global uniqueness and security.

## Core Entities

### `users`
Stores registered customer accounts.
- `id` (UUID)
- `email` (String, unique)
- `hashed_password` (String)
- `first_name`, `last_name`, `phone`

### `products`
The main catalog of items available for purchase.
- `id` (UUID)
- `name`, `slug` (String, unique)
- `brand` (String)
- `price`, `original_price` (Float)
- `inventory_count` (Integer)
- `category_id` (UUID, Foreign Key)

### `categories`
Logical grouping for products (e.g., Laptops, Accessories).
- `id` (UUID)
- `name`, `slug` (String)

### `carts` and `cart_items`
Tracks items users intend to purchase. Supports anonymous sessions via `session_id`.
- `id` (UUID)
- `user_id` (UUID, nullable for guests)
- `session_id` (String)
- `cart_items` table links to `products` with a `quantity`.

### `orders` and `order_items`
Immutable records of completed or pending purchases.
- `order_number` (String, unique)
- `status` (Enum: PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED)
- Pricing fields (`subtotal`, `tax_amount`, `shipping_charge`, `total_amount`)
- Denormalized shipping address snapshot (`shipping_name`, `shipping_city`, etc.) to preserve historical correctness.

### `payments`
Tracks transactions processed via Razorpay.
- `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`
- `amount` (Float, in INR), `amount_in_paise` (Integer)
- `status` (Enum: PENDING, SUCCESS, FAILED, REFUNDED)

### `events`
Immutable, append-only log designed for the **Agentic Commerce Copilot**. 
Records real-time behavioral data (clicks, views, searches) along with a `session_id`.
- `id` (UUID)
- `event_type` (Enum)
- `session_id` (String)
- `event_metadata` (JSON)

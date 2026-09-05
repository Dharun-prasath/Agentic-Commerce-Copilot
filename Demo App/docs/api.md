# REST API Documentation

The Demo App backend provides a FastAPI-based RESTful JSON API under the `/api/v1` namespace.

## Endpoints Overview

### Products (`/api/v1/products`)
- `GET /` — List products (supports filtering by `category`, `search` query, and pagination)
- `GET /{slug}` — Retrieve detailed product information by slug

### Cart (`/api/v1/cart`)
*Requires either `Authorization: Bearer <token>` OR an `X-Session-Id` header for anonymous users.*
- `GET /` — Retrieve current cart state
- `POST /add` — Add a product to the cart (requires `product_id`, `quantity`)
- `POST /update` — Update the quantity of a cart item
- `DELETE /remove/{item_id}` — Remove an item
- `POST /apply-coupon` — Apply a discount coupon to the cart subtotal

### Checkout (`/api/v1/checkout`)
- `POST /initiate` — Locks the cart and initiates the checkout process. Returns an order summary.

### Payments (`/api/v1/payments`)
- `POST /create-order` — Calls the Razorpay API to generate a `razorpay_order_id` for the total amount.
- `POST /verify` — Receives `razorpay_payment_id` and `razorpay_signature` from the frontend, verifies the signature against the Razorpay SDK, and marks the internal Order status as `CONFIRMED`.

### Telemetry / Events (`/api/v1/events`)
- `POST /` — Ingests behavioral data payloads from the frontend.
  - Expected schema includes `event_type` (e.g., `PAGE_VIEW`, `SEARCH`), `session_id`, and `event_metadata` JSON.

### Authentication (`/api/v1/auth`)
- `POST /register` — Register a new customer
- `POST /login` — Standard OAuth2 password flow, returns an access token
- `GET /me` — Retrieve the current authenticated user's profile

### Wishlist (`/api/v1/wishlist`)
*Requires Authentication.*
- `GET /` — List wishlist items
- `POST /add` — Add product to wishlist
- `DELETE /remove/{product_id}` — Remove from wishlist

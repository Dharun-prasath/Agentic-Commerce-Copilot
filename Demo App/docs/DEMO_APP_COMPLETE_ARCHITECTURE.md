# Demo App Complete Architecture

## 1. Executive Summary

The Demo App is a full-stack e-commerce application specializing in laptops, computers, and electronic accessories. It serves as a fully functional merchant platform intended to be integrated with the **Agentic Commerce Copilot**. The application provides a complete shopping experience including product catalog browsing, cart management, user authentication, checkout, and simulated/live payment processing via Razorpay. The system captures detailed customer behavioral data (events) designed to be consumed by an AI copilot.

**Technology Stack summary:** React 19 (Vite, TypeScript, Tailwind) on the frontend, and FastAPI (Python, SQLAlchemy, PostgreSQL) on the backend.

## 2. Complete Project Structure

```text
Demo App/
├── backend/
│   ├── alembic/                # Database migration scripts
│   ├── alembic.ini             # Alembic configuration
│   ├── app/
│   │   ├── api/                # FastAPI routers and endpoints
│   │   ├── core/               # Security, config, dependencies
│   │   ├── db/                 # Database session setup
│   │   ├── events/             # Event-related logic
│   │   ├── integrations/       # External integrations (e.g., Razorpay)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── repositories/       # Data access layer
│   │   ├── schemas/            # Pydantic models for request/response
│   │   ├── services/           # Business logic layer
│   │   └── main.py             # FastAPI application entry point
│   ├── scripts/                # Database seeders and utility scripts
│   ├── tests/                  # Pytest test suites
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Example environment variables
├── frontend/
│   ├── public/                 # Static assets and images
│   ├── src/
│   │   ├── assets/             # Bundled assets (SVGs, logos)
│   │   ├── components/         # React UI components (Radix UI, Tailwind)
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # Utility functions
│   │   ├── pages/              # Route-level components
│   │   ├── services/           # API and Event tracking services
│   │   ├── store/              # Zustand global state stores
│   │   ├── types/              # TypeScript definitions
│   │   ├── App.tsx             # Main React application component
│   │   └── main.tsx            # Frontend entry point
│   ├── package.json            # Node.js dependencies
│   ├── tailwind.config.js      # Tailwind CSS configuration
│   └── vite.config.ts          # Vite configuration
├── docs/                       # Project documentation
└── start.py                    # Master start script for frontend & backend
```

## 3. Technology Stack

| Layer | Technology | Version | Purpose | Verified From |
|------|------------|---------|---------|--------------|
| Frontend | React | ^19.2.8 | UI Library | package.json |
| Frontend Build | Vite | ^8.2.2 | Build Tool / Dev Server | package.json |
| Language | TypeScript | ~6.0.2 | Frontend Language | package.json |
| CSS | Tailwind CSS | ^4.3.3 | Styling | package.json |
| UI Components | Radix UI | Various | Accessible UI Primitives | package.json |
| State Mgmt | Zustand | ^5.0.15 | Global State Management | package.json |
| Data Fetching| React Query | ^5.102.4| API State Management | package.json |
| Backend | FastAPI | 0.115.5 | API Framework | requirements.txt |
| ORM | SQLAlchemy | 2.0.36 | Database ORM | requirements.txt |
| Migrations | Alembic | 1.14.0 | Database Migrations | requirements.txt |
| Database | PostgreSQL | N/A | Primary Data Store | models.py, env |
| DB Driver | asyncpg | 0.30.0 | Async Postgres Driver | requirements.txt |
| Data Validation| Pydantic | 2.10.3 | Request/Response Validation | requirements.txt |
| Authentication | python-jose, bcrypt| 3.3.0, 3.2.2 | JWT Generation and Hashing | requirements.txt |
| Payments | Razorpay | 1.4.2 | Payment Gateway Integration | requirements.txt |
| Testing | Pytest | 8.3.4 | Backend Testing | requirements.txt |

## 4. System Architecture

```text
       Browser (User)
             │
             ▼
    ┌─────────────────┐
    │  React Frontend │ (Port 5173)
    │  (Vite + SPA)   │
    └─────────────────┘
             │ HTTP / REST API
             ▼
    ┌─────────────────┐
    │ FastAPI Backend │ (Port 8001)
    │  (Uvicorn)      │
    └─────────────────┘
             │ Asyncpg
             ▼
    ┌─────────────────┐
    │   PostgreSQL    │ (Port 5432)
    │   Database      │
    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │External Services│
    │ (Razorpay API)  │
    └─────────────────┘
```
*Note: Frontend event tracking currently fires directly to the external Agentic Copilot port (8000).*

## 5. Backend Architecture

- **Application Entry Point:** `backend/app/main.py` initializes the FastAPI `app`, mounts CORS middleware, and includes the `api_router`.
- **API Structure:** Versioned under `/api/v1`. Routers are aggregated in `app/api/v1/__init__.py`.
- **Routers:** Endpoints are logically separated into files like `auth.py`, `products.py`, `cart.py`, `commerce.py`, `events.py`.
- **Services:** Business logic lives in `app/services/` (e.g., `cart_service.py`, `payment_service.py`). Services handle data manipulation.
- **Repositories:** Data access layer pattern is established in `app/repositories/` but SQLAlchemy queries are frequently executed within the services.
- **Models:** Defined in `app/models/models.py`. SQLAlchemy declarative base is used. Models utilize UUIDs as primary keys.
- **Schemas:** Pydantic models in `app/schemas/` handle data validation for API requests and responses.
- **Authentication:** Managed via JWT tokens (Bearer). Handled by `auth_service.py` and `deps.py` dependencies. Anonymous users are tracked via `X-Session-Id`.
- **Error Handling:** Global exception handler in `main.py` catches all unhandled exceptions and returns a structured 500 JSONResponse.
- **Configuration:** Managed by `pydantic-settings` in `core/config.py`, loading variables from the `.env` file.
- **Database Connection:** Asynchronous SQLAlchemy session factory setup in `db/session.py`.
- **Migrations:** Alembic is configured in `alembic/env.py` pointing to SQLAlchemy `Base.metadata`.

Request Flow: Request ➔ FastAPI Router ➔ Dependency Injection (Auth/DB) ➔ Service Layer ➔ SQLAlchemy ➔ PostgreSQL.

## 6. Complete API Inventory

| Method | Endpoint | Purpose | Auth Required | Source File |
|--------|----------|---------|---------------|-------------|
| GET | `/` | Health check | No | `main.py` |
| GET | `/health` | Health check | No | `main.py` |
| POST | `/api/v1/auth/login` | Authenticate user | No | `endpoints/auth.py` |
| POST | `/api/v1/auth/register` | Register new user | No | `endpoints/auth.py` |
| GET | `/api/v1/products` | List/search products | No | `endpoints/products.py` |
| GET | `/api/v1/products/{slug}` | Get product details | No | `endpoints/products.py` |
| GET | `/api/v1/cart` | Get user/session cart | Optional | `endpoints/cart.py` |
| POST | `/api/v1/cart/items` | Add item to cart | Optional | `endpoints/cart.py` |
| PATCH| `/api/v1/cart/items/{id}`| Update item qty | Optional | `endpoints/cart.py` |
| DELETE|`/api/v1/cart/items/{id}`| Remove item | Optional | `endpoints/cart.py` |
| DELETE| `/api/v1/cart` | Clear entire cart | Optional | `endpoints/cart.py` |
| POST | `/api/v1/cart/coupon` | Apply coupon | Optional | `endpoints/cart.py` |
| GET | `/api/v1/wishlist` | Get user wishlist | Yes | `endpoints/wishlist.py` |
| POST | `/api/v1/wishlist/items` | Add to wishlist | Yes | `endpoints/wishlist.py` |
| DELETE|`/api/v1/wishlist/items/{id}`| Remove from wishlist | Yes | `endpoints/wishlist.py` |
| POST | `/api/v1/events` | Ingest behavioral event | No | `endpoints/events.py` |
| GET | `/api/v1/events` | Query stored events | No | `endpoints/events.py` |
| POST | `/api/v1/checkout/addresses` | Add user address | Yes | `endpoints/commerce.py` |
| GET | `/api/v1/checkout/addresses` | Get user addresses | Yes | `endpoints/commerce.py` |
| POST | `/api/v1/checkout/initiate` | Initialize checkout | Yes | `endpoints/commerce.py` |
| POST | `/api/v1/payments/create` | Create Razorpay order | Yes | `endpoints/commerce.py` |
| POST | `/api/v1/payments/verify` | Verify payment & place order | Yes | `endpoints/commerce.py` |
| GET | `/api/v1/orders` | Get user orders | Yes | `endpoints/commerce.py` |
| GET | `/api/v1/orders/{id}` | Get order details | Yes | `endpoints/commerce.py` |

*(Note: Request/Response schemas map to Pydantic classes defined in `app/schemas/`)*

## 7. Database Architecture

**Database Technology:** PostgreSQL
**ORM:** SQLAlchemy 2.0 (asyncpg)

### Core Tables & Models
- `users`: id, email, password_hash, name, phone, roles.
- `addresses`: id, user_id (FK), delivery details.
- `categories`: Hierarchical categories (parent_id FK).
- `brands` & `series`: Brand classification structure.
- `product_models`: Product line identifier.
- `products`: SKU level product. Contains JSON specifications and features, stock, price, category_id.
- `product_compatibilities`: self-referential many-to-many on products for accessories.
- `product_images`: id, product_id, url.
- `product_reviews`: id, product_id, user_id, rating.
- `wishlists` & `wishlist_items`: User wishlists.
- `carts` & `cart_items`: Cart structure. Supports `user_id` and anonymous `session_id`.
- `coupons`: Discount codes and constraints.
- `orders` & `order_items`: Immutable order records with denormalized snapshots of pricing/shipping.
- `payments`: Razorpay transaction tracking.
- `events`: Append-only immutable event log (Copilot integration).

*All primary keys use UUID strings.*

## 8. Product System

Products follow a hierarchical metadata structure:
`Category` -> `Brand` -> `Series` -> `ProductModel` -> `Product` (SKU).
- **Product Model:** The actual SKU holding price (`price`, `original_price`), stock, specifications (`JSON` dict), features (`JSON` list), tags.
- **Images:** One-to-many relationship (`ProductImage`), supports primary flag.
- **Compatibility:** `ProductCompatibility` maps accessories and recommended products to a source product.
- **Reviews:** Handled via `ProductReview` model (aggregated rating cached on `Product`).

## 9. Customer Behaviour Tracking

The frontend uses `tracker.ts` to fire-and-forget events.
**IMPORTANT:** The frontend tracker currently sends POST requests to `http://localhost:8000/api/v1/integration/events`, which assumes the Agentic Copilot is running on port 8000, not the Demo App backend (port 8001).

| Event | Trigger | Data Captured | API | Source |
|------|---------|--------------|-----|--------|
| `CART_ITEM_ADDED` | Adding item to cart | `product_id`, `quantity` | Copilot (8000) | `cartStore.ts` |
| `CART_UPDATED` | Changing cart qty | `item_id`, `quantity` | Copilot (8000) | `cartStore.ts` |
| `CART_ITEM_REMOVED`| Removing cart item | `item_id` | Copilot (8000) | `cartStore.ts` |

*(Note: Other events in the `EventType` enum like `PRODUCT_VIEWED`, `PRODUCT_SEARCHED` exist in the backend schema, but the actual frontend triggers for these appear partially implemented or reliant on manual calls.)*

## 10. Frontend Architecture

- **Entry Point:** `src/main.tsx` renders `App.tsx`.
- **Routing:** React Router v6 handles client-side routing. Protected routes wrap authenticated pages.
- **State Management:** `Zustand` manages global state (`authStore.ts`, `cartStore.ts`, `wishlistStore.ts`).
- **Data Fetching:** Axios instance (`services/api.ts`) with request interceptors for JWT and `X-Session-Id`.
- **UI Architecture:** Tailwind CSS + Radix UI primitives. Page components assemble UI from `src/components/`.

## 11. Complete User Journey

1. **Landing:** `HomePage.tsx` -> Displays hero and featured categories.
2. **Product Listing:** `ProductsPage.tsx` -> Fetches `/api/v1/products`.
3. **Product Details:** `ProductDetailPage.tsx` -> Fetches `/api/v1/products/{slug}`.
4. **Cart:** User adds item -> `cartStore.ts` fires `/api/v1/cart/items` -> `CART_ITEM_ADDED` event tracked.
5. **Checkout:** `CheckoutPage.tsx` -> Collects address (`/api/v1/checkout/addresses`).
6. **Payment:** Calls `/api/v1/payments/create` -> Opens Razorpay Modal -> On success, calls `/api/v1/payments/verify`.
7. **Order:** Redirects to `PaymentSuccessPage.tsx` -> View details in `OrdersPage.tsx`.

## 12. Payment System

- **Provider:** Razorpay.
- **Flow:**
  1. Frontend calculates total.
  2. Backend `/api/v1/payments/create` hits Razorpay API to generate an Order ID.
  3. Frontend opens Razorpay UI with the Order ID.
  4. Upon user payment, Razorpay returns a signature.
  5. Frontend posts signature to `/api/v1/payments/verify`.
  6. Backend verifies signature with Razorpay Secret.
  7. If valid, Backend converts `Cart` to `Order`, clears `Cart`, and marks `Payment` as `PAID`.

## 13. Authentication & Users

- **Registration/Login:** `auth_service.py` handles password hashing (bcrypt) and JWT generation (python-jose).
- **Session:** Bearer token stored in `localStorage` (`access_token`).
- **Authorization:** `get_current_user` dependency enforces authentication on protected routes (Orders, Wishlist, Checkout).
- **Roles:** `is_admin` boolean flag on `User` model (not heavily utilized in frontend currently).

## 14. Environment Configuration

| Variable | Purpose | Required | Example/Format | Used By |
|----------|---------|----------|----------------|---------|
| `DATABASE_URL` | Postgres connection | Yes | `postgresql://user:pass@host:5432/db` | Backend DB |
| `JWT_SECRET` | Token signing secret | Yes | `random-string` | Backend Auth |
| `JWT_ALGORITHM`| Token algorithm | No | `HS256` | Backend Auth |
| `JWT_EXPIRE_MINUTES`| Token expiry time | No | `10080` | Backend Auth |
| `RAZORPAY_KEY_ID` | Razorpay API Key | No (Warns) | `rzp_test_...` | Backend Payments|
| `RAZORPAY_KEY_SECRET`| Razorpay Secret | No (Warns) | `secret_...` | Backend Payments|
| `APP_PORT` | Backend binding port| No | `8001` | `main.py` |
| `FRONTEND_URL` | CORS allowance | No | `http://localhost:5173` | Backend CORS |

## 15. Running the Application

A master script is provided at the root:
```bash
# Starts both frontend and backend automatically
python3 start.py
```
**Actual Ports verified by script:**
- **Backend:** `http://localhost:8001` (Uvicorn)
- **Frontend:** `http://localhost:5173` (Vite)

## 16. Existing Integrations

1. **Razorpay:** For payment processing in checkout flow.
2. **Agentic Commerce Copilot:** The frontend `tracker.ts` is explicitly hardcoded to send behavioral events to the Copilot backend at `http://localhost:8000`.

## 17. Testing

- **Framework:** Pytest, pytest-asyncio.
- **Files:** Located in `Demo App/backend/tests/` and root `test_*.py` files.
- **Commands:** Run `pytest` within the backend directory. Coverage metrics are not explicitly configured via scripts.

## 18. Current Limitations

- **UNKNOWN:** Comprehensive trigger hooks for behavioral tracking on the frontend (e.g. `PRODUCT_VIEWED`) exist in the schema but firing locations are not completely verified across all components.
- **PARTIALLY IMPLEMENTED:** `tracker.ts` hardcodes `localhost:8000` assuming the Copilot is running locally.

## 19. Integration Surface for Agentic Copilot

**EXISTING INTEGRATION POINTS:**
- **Product Catalog:** Copilot can consume `/api/v1/products` for context retrieval.
- **Cart Manipulation:** Copilot can use `/api/v1/cart` endpoints leveraging the `X-Session-Id` header to modify customer carts remotely.
- **Event Consumption:** The Demo App's `tracker.ts` actively pushes events to the Copilot's `/api/v1/integration/events` endpoint on port 8000.
- **Event History:** Copilot can query historical events from the Demo App via `/api/v1/events`.

**MISSING INTEGRATION POINTS:**
- No bidirectional Webhook system for Copilot to receive real-time order status updates from the Demo App natively (beyond standard REST polling).
- Cross-origin authentication handshakes if Copilot needs to act explicitly on behalf of a logged-in user without raw credentials.

## 20. Data Flow Diagram

*(A) Product View Flow*
```text
Browser -> GET /products/{slug} -> ProductService -> DB -> Frontend (Render) -> trackEvent(PRODUCT_VIEWED) -> Copilot (8000)
```

*(B) Checkout Flow*
```text
Browser -> POST /payments/create -> Backend -> Razorpay (Create Order) -> Razorpay ID -> Browser -> Razorpay UI -> Browser -> POST /payments/verify -> Backend -> DB (Create Order, Clear Cart)
```

## 21. Agentic Commerce Integration Readiness

| Capability | Status | Existing API | Missing Requirement |
|------------|--------|--------------|---------------------|
| Product Search | Ready | `/api/v1/products` | None |
| Product Details| Ready | `/api/v1/products/{slug}`| None |
| Customer Activity| Partially Ready | `/api/v1/events` | More granular frontend triggers |
| Wishlist | Ready | `/api/v1/wishlist` | None |
| Cart | Ready | `/api/v1/cart` | None |
| Checkout | Ready | `/api/v1/checkout/initiate`| None |
| Payment | Ready | `/api/v1/payments/verify` | None |

## 22. Final Implementation Status

- **Database Models & ORM:** DONE
- **Authentication System:** DONE
- **Product Catalog API:** DONE
- **Cart & Wishlist Logic:** DONE
- **Checkout & Payments:** DONE
- **Behavioral Tracking:** PARTIALLY DONE (Backend ready, frontend triggers limited, hardcoded Copilot port).
- **Test Coverage:** UNKNOWN (Tests exist but completeness is unverified).

*Documentation generated from the current source code.*

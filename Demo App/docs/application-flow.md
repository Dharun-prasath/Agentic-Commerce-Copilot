# Application Flow

The Demo Commerce Application implements a standard, full-featured e-commerce lifecycle, from browsing to payment.

## 1. Browsing & Telemetry

1. The user navigates to the React frontend.
2. The frontend generates a unique `X-Session-Id` and persists it in local storage.
3. As the user navigates between pages (`/`, `/products`, `/products/:slug`), the frontend automatically fires `PAGE_VIEW`, `SEARCH`, and `PRODUCT_VIEW` events.
4. These events are sent asynchronously to `/api/v1/events` and saved in the PostgreSQL database.
5. *Integration Point:* The Agentic Copilot Orchestrator continuously monitors this event stream.

## 2. Cart Management

1. The user clicks "Add to Cart" on a product.
2. The frontend POSTs to `/api/v1/cart/add`, attaching the `X-Session-Id`.
3. The backend resolves the user's cart (or creates a new one), inserts the item, and recalculates pricing (subtotal, tax).
4. The frontend fetches the updated cart state and renders the cart drawer.

## 3. Checkout

1. From the cart, the user proceeds to Checkout.
2. The frontend calls `/api/v1/checkout/initiate`.
3. The backend verifies inventory, locks the cart, and prepares an `Order` record with a `PENDING` status.
4. The user is prompted to enter shipping details (or select a saved address if logged in).

## 4. Payment via Razorpay

1. The user clicks "Pay Now".
2. The frontend calls `/api/v1/payments/create-order`, passing the internal `order_id`.
3. The backend makes an API call to the Razorpay Server, returning a `razorpay_order_id`.
4. The frontend uses the Razorpay JS SDK to render the payment modal.
5. The user completes the payment in the modal.
6. Razorpay redirects/callbacks to the frontend with a `razorpay_payment_id` and a `razorpay_signature`.
7. The frontend POSTs these details to `/api/v1/payments/verify`.
8. The backend cryptographically verifies the signature using its `RAZORPAY_KEY_SECRET`.
9. If valid, the backend updates the Order status to `CONFIRMED`.
10. The user is redirected to a success page.

## 5. Agentic Copilot Intervention

If the user is interacting with the **Agentic Commerce Copilot** (e.g. via Voice or Telegram):

1. The user speaks to the AI Sales Consultant: *"Add the MacBook Air to my cart."*
2. The Copilot's `CommerceEngine` bypasses the frontend and directly hits the Demo App's API or Database.
3. The Copilot adds the item to the cart using the user's `session_id`.
4. Because the frontend uses React Query / Zustand polling or SSE (if implemented), the cart UI immediately updates in the user's browser, demonstrating a seamless omni-channel experience.

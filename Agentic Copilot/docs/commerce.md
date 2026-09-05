# Commerce Engine Flow

The **Commerce Engine** is the deterministic bridge between the stochastic Agentic Copilot and the rigid backend database of the Demo App. It is responsible for safely executing transactions on behalf of the customer.

## Location
- `app/services/commerce/engine.py`

## The Execution Flow (Add to Cart)

1. **Trigger**: When the Voice Agent outputs a `confirm_product_selection` tool call containing a `product_id`, the Voice Provider intercepts it and asks the Orchestrator to execute a Commerce action.
2. **Direct Database Connection**: For maximum security and speed, the Commerce Engine does not make an HTTP request to the Demo App. Instead, it uses a dedicated async SQLAlchemy engine to connect directly to the Demo App's PostgreSQL database (`COMMERCE_DATABASE_URL`).
3. **Session Resolution**: It attempts to find the `user_id` associated with the current Copilot `CustomerSession`.
4. **Validation Phase**:
   - It runs a `SELECT` query against the `products` table using the provided `product_id`.
   - If the product does not exist, it throws a `COMMERCE_DB_ERROR`. This error bubbles all the way back to the Voice Agent, instructing the LLM to apologize and ask the user to pick again.
5. **Cart Resolution**:
   - If a `user_id` exists, it looks for an existing cart for that user.
   - If no user is logged in (anonymous mode), it attempts to find the most recently active cart or creates a fallback cart.
6. **Execution Phase**:
   - It checks if the item is already in the `cart_items` table.
   - If it is, it increments the `quantity` via an `UPDATE` statement.
   - If not, it generates a new UUID and runs an `INSERT` statement.
7. **Omni-Channel Result**: Because the transaction hits the database directly, if the user happens to have the merchant website open on their laptop, React Query will instantly reflect the updated cart in their browser, completing the "magic" of the Agentic Commerce Copilot.

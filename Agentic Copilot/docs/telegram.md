# Telegram Engine Flow

The **Telegram Engine** allows the Agentic Commerce Copilot to push highly formatted, interactive product cards to the customer's phone asynchronously.

## Location
- `app/integrations/telegram/provider.py`

## The Execution Flow

1. **Trigger**: When the Orchestrator receives recommendations from the `ProductIntelligenceAgent`, it immediately runs a background task to push these to Telegram.
2. **Customer Lookup**: The backend checks the `CustomerSession` for the `user_id`, then looks up the `Customer` record to find the `telegram_chat_id`. 
   - *Note: In the Demo app, if a chat ID is missing, it falls back to a hardcoded test ID (2019487070).*
3. **Card Generation (`send_product_card`)**:
   - For each recommended product, the Engine escapes strings to prevent HTML injection.
   - It formats the price, calculates discount percentages, and constructs star emojis for ratings.
   - It builds an **Inline Keyboard** (a Telegram feature) that contains a deep link (e.g., `https://example.com/products/dell-xps-15`) allowing the user to tap and immediately open the product on the merchant website.
   - It attempts to download the product's thumbnail image using `httpx`.
4. **Dispatch**:
   - If the image downloads successfully, it uses the Telegram `sendPhoto` endpoint with the HTML text as the caption.
   - If the image fails or doesn't exist, it falls back to the `sendMessage` endpoint.
5. **Parallelism**: Multiple product cards are pushed concurrently using `asyncio.gather` to ensure they all arrive instantly.

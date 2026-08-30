# Intent Intelligence Testing Guide

This document describes how to test the Intent Intelligence Pipeline.

## Manual Test Procedure

1. **Start the Systems:**
   - Agentic Copilot Backend: `python start.py`
   - Agentic Copilot Frontend Dashboard (`npm run dev`)
   - Demo App Frontend & Backend (`npm run dev`)

2. **Create a Customer Session:**
   - Open the Demo App in a browser.
   - Login as a user (this binds the session to a `customer_id`).

3. **Perform Behaviors & Verify Real-Time Score:**
   - Open the Copilot Dashboard in another window side-by-side.
   - In the Demo App:
     - Search for "gaming laptop".
     - View a product (e.g., ASUS ROG).
     - Switch tabs to Specifications, Features, and Reviews.
     - Add the product to the wishlist.
     - Go back and view a different product (e.g., Lenovo Legion).
   - In the Copilot Dashboard:
     - Observe the "Customer 360 View" for your active session.
     - The **Live Intent Score** should increase for each of these actions.
     - The status should say **ACTIVE SESSION**.
     - Verify that refreshing the *same* product page repeatedly does *not* continuously increase the score (Anti-Spam check).

4. **Session Termination & Intent Agent Hand-off:**
   - The threshold is 50 by default. Ensure your score is > 50.
   - In the Demo App, close the browser tab. This triggers the `beforeunload` event, sending `SESSION_TERMINATED`.
   - In the Copilot Dashboard:
     - The status should change to **SESSION TERMINATED**.
     - The Intent Agent status should change to **TRIGGERED**.

5. **Verify Logs:**
   - Check the `logs/intent/` directory in the `Agentic Copilot/backend/` root.
   - `intent_events.jsonl`: Contains line-by-line delta updates for your actions.
   - `intent_sessions.jsonl`: Contains the final session record.
   - `intent_agent_inputs.jsonl`: Contains the exact structured JSON payload sent to Gemini.
   - `intent_agent_outputs.jsonl`: Contains the Gemini output with `intent_category`, `reasoning`, and `sales_consultant_context`.

6. **Verify Constraints:**
   - The Sales Consultant electron window **MUST NOT** appear.
   - The Telegram bot **MUST NOT** send any messages.
   - The LLM should strictly return JSON matching the `StructuredIntentOutput` schema.

## Automated Testing Strategy

To run the automated tests:
```bash
cd backend
pytest tests/test_intent_scorer.py
```

The tests cover:
- Real-time scoring math.
- Anti-spam rules.
- Proper threshold crossing logic without premature LLM invocation.
- Session finalization logic correctly invoking the real Intent Agent API (no mocks allowed). Tests that require Gemini use the real configured API to explicitly separate live integration from deterministic unit tests.

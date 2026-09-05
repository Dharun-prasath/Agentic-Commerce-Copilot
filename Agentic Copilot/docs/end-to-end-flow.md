# End-to-End Walkthrough

This document traces a complete, real-world scenario of the Agentic Commerce Copilot in action.

## The Scenario

1. **The Web Experience (Telemetry)**
   - The customer visits the Demo App (React Frontend).
   - They search for "gaming laptop". The frontend emits a `SEARCH` event to the Copilot.
   - They click on the "Dell XPS 16" and spend 45 seconds on the page. The frontend emits `PRODUCT_VIEW` and `TIME_SPENT` events.
   - They add it to their cart, but then remove it.
   - They close the browser tab. The frontend emits a `SESSION_TERMINATED` event.

2. **The Intent Agent (Analysis)**
   - The Copilot's `Orchestrator` receives the termination event.
   - It calculates a deterministic intent score based on the high-value item views. The score exceeds the threshold.
   - The `QueueManager` triggers the `IntentAgent`.
   - The LLM analyzes the JSON session summary and outputs:
     - `intent_category`: "HIGH_PURCHASE_INTENT"
     - `recommended_action`: "INITIATE_SALES_CONVERSATION"
     - `sales_consultant_context`: "Customer was looking at the Dell XPS 16 but abandoned the cart. They are likely price sensitive or unsure about specs."

3. **The Voice Agent (Consultation)**
   - The `Orchestrator` pushes a trigger to the local Electron App.
   - The Electron App "rings" on the desktop. The user answers.
   - The `SalesConsultantAgent` connects via WebSocket.
   - **AI (Voice)**: *"Hi there! I noticed you were looking at the Dell XPS 16 earlier. Was there anything specific holding you back?"*
   - **Customer (Voice)**: *"Yeah, it's a bit too expensive. Do you have anything similar but cheaper?"*
   - The LLM outputs a tool call: `request_product_recommendations({"budget_max": 2000, "category": "laptop"})`.

4. **Product Intelligence (Curation)**
   - The `Orchestrator` intercepts the tool call and runs the `ProductIntelligenceAgent`.
   - The Agent fetches the catalog, parses the specs, and finds a cheaper alternative.
   - It returns the "ASUS ROG Zephyrus" to the Orchestrator.

5. **Omni-Channel Handoff (Execution)**
   - The `Orchestrator` passes the recommendation back to the Voice Agent.
   - **AI (Voice)**: *"I found the ASUS ROG Zephyrus. It has similar specs but is much more affordable. I've just sent a card with the details to your Telegram. Would you like me to add it to your cart?"*
   - Meanwhile, the `TelegramEngine` fires asynchronously, delivering a beautiful HTML card with an image and a "View Product" deep link to the user's phone.
   - **Customer (Voice)**: *"Yes, please add it."*
   - The LLM outputs a tool call: `confirm_product_selection({"product_id": "..."})`.
   - The `CommerceEngine` intercepts this, bypasses the APIs, and forcefully writes the item into the actual PostgreSQL database of the Demo App.
   - The user opens their laptop, refreshes the Demo App, and the ASUS ROG is magically in their cart, ready for checkout.

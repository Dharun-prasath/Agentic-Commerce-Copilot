# Agentic Commerce Copilot

Welcome to the **Agentic Commerce Copilot** repository. This project is a complete, end-to-end demonstration of next-generation AI in e-commerce.

It consists of two massive, decoupled applications that work together to create a seamless, omni-channel shopping experience:

## 1. Demo Commerce App (`/Demo App`)
A fully functional, modern e-commerce platform built with React, FastAPI, and PostgreSQL. It acts as the testing ground, emitting behavioral telemetry and exposing backend APIs.

👉 **[Read the Demo App Documentation](./Demo%20App/docs/README.md)**

## 2. Agentic Copilot (`/Agentic Copilot`)
The AI orchestrator. It sits alongside the merchant website, silently monitoring user behavior until it detects purchase intent. Once triggered, it spins up specialized AI Agents (Intent, Product Intelligence, Sales Consultant) to proactively assist the customer over Voice and Telegram.

👉 **[Read the Agentic Copilot Documentation](./Agentic%20Copilot/docs/README.md)**

---

## How It Works (The 10,000 ft View)

1. **Telemetry**: As users browse the `Demo App`, silent events (clicks, views, time spent) are streamed to the `Agentic Copilot`.
2. **Intent Scoring**: The Copilot calculates a deterministic intent score. If a user lingers on expensive items but abandons their cart, the score spikes.
3. **Agent Orchestration**: The Copilot wakes up its **Intent Agent** (Gemini 1.5 Pro) to analyze the raw JSON events and generate a "Mock Customer Requirement".
4. **Proactive Outreach**: The Copilot triggers a "phone call" (via the Electron App UI). A **Sales Consultant Agent** (Gemini 2.5 Flash Native Audio) greets the user based on the generated context.
5. **Product Intelligence**: When the user asks for alternatives over the phone, the Copilot triggers the **Product Intelligence Agent** to search the Demo App's catalog and find the perfect match.
6. **Omni-Channel Execution**: 
   - The Copilot sends a beautiful HTML product card to the user's **Telegram** asynchronously.
   - If the user says "Yes, add it", the Copilot's **Commerce Engine** connects directly to the Demo App's database and inserts the item into the cart.
   - The React frontend instantly updates, completing the loop.

---

## Quick Start

You can run both applications concurrently using the root startup script.

```bash
# Start the Backend (Demo App API + Copilot API + React Vite Server)
python3 "Agentic Copilot/start.py" & python3 "Demo App/start.py"

# Start the Phone UI (Electron Voice Client)
python3 "Agentic Copilot/start_electron.py"
```

## Disclaimer
This is a demonstration project created for a Buildathon. Please ensure you configure your API keys in the respective `.env` files before running.

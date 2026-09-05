# Execution Engines Overview

While Agents (Intent, Product Intelligence, Sales Consultant) are stochastic and LLM-driven, **Execution Engines** are deterministic, traditional code blocks. They exist to translate the decisions made by AI agents into hard, undeniable reality (like modifying a database or hitting a third-party API).

The Orchestrator strictly controls when these engines are invoked.

## 1. Commerce Engine
**Purpose**: Safely execute commerce transactions on behalf of the customer.
**Location**: `app/services/commerce/engine.py`
**Actions**: 
- `add_to_cart`: Connects directly to the Demo App's PostgreSQL database (`COMMERCE_DATABASE_URL`), bypasses the HTTP API for security/speed, and strictly verifies the `product_id` against the catalog before inserting a `cart_item` record.

## 2. Telegram Engine
**Purpose**: Deliver rich, asynchronous product cards to the customer's mobile device while they are on the phone with the Voice Agent.
**Location**: `app/integrations/telegram/provider.py`
**Actions**:
- `send_product_card`: Uses the Telegram Bot API (`https://api.telegram.org/bot<TOKEN>`) to send an HTML-formatted message block with inline buttons and images.
- `send_recommendation_summary`: Batches multiple product cards and sends them in a thread.

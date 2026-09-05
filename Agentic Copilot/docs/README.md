# Agentic Commerce Copilot

## Overview

The Agentic Commerce Copilot is an AI-driven orchestrator designed to run alongside a traditional e-commerce application (the "Demo App"). It listens to real-time customer behavior (telemetry), predicts purchasing intent, and activates autonomous AI agents to proactively assist the customer.

By combining deterministic event-processing with stochastic LLM-driven agents, the Copilot seamlessly bridges the gap between passive web browsing and high-touch, consultative sales via Voice and Telegram.

## Core Capabilities

1. **Intent Intelligence**: Monitors web events (e.g., viewing a high-value laptop multiple times) and scores the customer's intent to purchase in real-time.
2. **Multi-Agent Orchestration**: Routes tasks between specialized AI agents (Intent, Product Intelligence, Sales Consultant) to fulfill customer needs.
3. **Real-time Voice Interactions**: Integrates with the Gemini Live API via WebSockets to provide sub-second conversational voice assistance.
4. **Asynchronous Deliverables**: Generates rich product cards and pushes them to the customer's Telegram while the voice conversation is ongoing.
5. **Deterministic Commerce Execution**: Safely translates ambiguous LLM decisions into strict database transactions (e.g., adding to cart).

## System Components

### The Orchestrator
The `QueueManager` and `Orchestrator` form the central nervous system, consuming events, creating `OrchestratorJob` records, and dispatching work to the appropriate Agent or Engine based on the current state.

### Specialized Agents
- **Intent Agent**: Synthesizes a massive array of behavioral events into a coherent "Mock Customer Requirement" (e.g., "Customer wants a gaming laptop under $1500").
- **Product Intelligence Agent**: Takes requirements, executes semantic searches against the product catalog, and selects the absolute best matches.
- **Sales Consultant Agent**: A Voice-native agent that talks to the customer, presents the curated recommendations, and negotiates the final decision.

### Execution Engines
- **Commerce Engine**: Securely bridges the Copilot to the Demo App's API. It handles operations like `add_to_cart` and enforces strict product ID validation.
- **Telegram Engine**: Pushes highly formatted HTML product cards and comparison summaries to the user's Telegram chat.

## Documentation Navigation

- [System Architecture](architecture.md)
- [Orchestrator Deep Dive](orchestrator.md)
- [Agents Breakdown](agents.md)
- [Engines Breakdown](engines.md)
- [Product Intelligence Flow](product-intelligence.md)
- [Sales Consultant Flow](sales-consultant.md)
- [Telegram Flow](telegram.md)
- [Commerce / Cart Flow](commerce.md)
- [End-to-End Walkthrough](end-to-end-flow.md)
- [Setup & Configuration](setup.md)

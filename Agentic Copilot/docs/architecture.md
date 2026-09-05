# System Architecture

The Agentic Commerce Copilot is built as an asynchronous, event-driven orchestration layer that sits adjacent to the traditional merchant application.

## High-Level Design

### Core Backend (FastAPI + PostgreSQL)
- **Framework**: FastAPI (Python), entirely async.
- **Database**: PostgreSQL (using SQLAlchemy 2.0 ORM).
- **Communication**: WebSockets (for Voice), HTTP REST (for Telegram & Internal APIs).

### The Four Pillars
The architecture is separated into four distinct pillars to separate AI stochasticity from deterministic logic:

1. **Observability & Intent (Telemetry)**
   - The Copilot exposes an `/api/v1/integration/events` endpoint. The frontend Demo App streams user clicks, page views, and searches to this endpoint.
   - The events are stored immutably.
2. **The Orchestrator & State Machine**
   - A rigid, rule-based state machine (`OrchestratorJob`) that ensures the multi-agent workflow doesn't break.
   - A `QueueManager` acts as a background worker thread to process long-running LLM inferences without blocking the API.
3. **AI Agents (The Brains)**
   - `IntentAgent`: Analyzes session history to output a structured Intent Assessment.
   - `ProductIntelligenceAgent`: Maps requirements to the catalog.
   - `SalesConsultantAgent`: Connects to Gemini Live API via WebSockets for real-time voice.
4. **Execution Engines (The Hands)**
   - `CommerceEngine`: Connects directly to the Demo App DB to perform deterministic writes (e.g. Add to Cart).
   - `TelegramEngine`: Uses external HTTP APIs to send messages.

## Architectural Flow
```
[User Web Browser] -> (Telemetry) -> [Copilot Event API]
                                          |
                                    [Orchestrator]
                                    /     |      \
                           [Intent]  [Product]  [Voice]
                                          |
                                    [Orchestrator]
                                    /            \
                           [Commerce Engine]   [Telegram Engine]
                                   |                   |
                           [Demo App DB]       [Telegram API]
```

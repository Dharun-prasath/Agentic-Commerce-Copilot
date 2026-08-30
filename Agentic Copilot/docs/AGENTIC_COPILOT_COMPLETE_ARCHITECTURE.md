# Agentic Copilot Complete Architecture

## 1. Executive Summary

Agentic Copilot is the AI orchestration backend and dashboard for the Agentic Commerce platform.

**Current Purpose:** It ingests behavioral events from the Demo App, evaluates purchase intent using LLMs, triggers LangGraph workflows, and interacts with the user via a simulated Electron phone call (Gemini Native Audio) or Telegram. It provides a React dashboard to monitor these active sessions.

**Intended Purpose:** A fully autonomous commerce agent that tracks customer behavioral signals (search, view, cart) with rule-based heuristics, triggers an LLM for intent validation when a threshold is met, and seamlessly intervenes to assist customers via Voice or Chat.

**Current Capabilities:**
- Ingests events via REST API.
- LangGraph orchestration with PostgreSQL checkpointing.
- Intent evaluation via Gemini structured output (Agent).
- Voice communication via an Electron desktop simulation hooked into Gemini 2.5 Flash Native Audio.
- Telegram text-based consultation.
- Commerce tool execution (Search, Details, Cart).
- Dashboard polling for live Customer 360 view.

**Current Limitations:**
- **No Rule-Based Intent Scoring:** The intended rule-based heuristic trigger is missing. LangGraph currently executes on every event and invokes the LLM intent agent directly.
- **Polling Dashboard:** The React dashboard relies on 3s interval polling rather than WebSocket/SSE for real-time updates.
- **Hardcoded Integration:** The Demo App's `tracker.ts` directly hardcodes the Copilot's `localhost:8000` port.

---

## 2. Complete Project Structure

```text
Agentic Copilot/
├── backend/
│   ├── alembic/                # Database migrations engine
│   ├── alembic_dir/            # Migration versions and scripts
│   ├── app/
│   │   ├── agents/             # Prompts & Langchain definitions (Commerce, Intent, Product, Sales)
│   │   ├── api/                # FastAPI endpoints (Dashboard, Events, Telegram, Voice, System)
│   │   ├── core/               # DB setup, Config, Security, Middleware
│   │   ├── events/             # (Empty/unused module)
│   │   ├── graph/              # LangGraph orchestration (orchestrator.py)
│   │   ├── integrations/       # Providers (Telegram, Voice, Demo App client)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── repositories/       # (Empty/unused module)
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Background tasks (event_processor.py)
│   │   └── main.py             # FastAPI entry point
│   ├── tests/                  # Pytest integration tests
│   ├── alembic.ini             # Alembic configuration
│   └── requirements.txt        # Python dependencies
├── electron/
│   ├── src/                    # React UI for the simulated phone call (App.tsx)
│   ├── main.js                 # Electron main process & trigger server (Port 3456)
│   ├── preload.cjs             # IPC exposure for window hiding / call triggers
│   └── package.json            # Node dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # React UI (Customer360, AgentsConfigView, SessionRow)
│   │   ├── assets/             # Static SVGs and Images
│   │   └── App.tsx             # Main dashboard layout
│   └── package.json            # Node dependencies
├── docs/                       # Project documentation
├── scripts/                    # Utility scripts
├── docker-compose.yml          # PostgreSQL and Redis infrastructure
├── start.py                    # Starts Backend (8000) and Frontend (5174)
└── start_electron.py           # (Utility script)
```

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose | Verified From |
|------|------------|---------|---------|--------------|
| Backend API | FastAPI | - | REST framework | backend/app/main.py |
| DB / ORM | PostgreSQL / SQLAlchemy| - | Data Persistence | backend/app/models/ |
| AI Orchestration| LangGraph | - | State machine execution | backend/app/graph/ |
| AI Models | Gemini / LangChain | - | Intent & Sales Agents | backend/app/agents/ |
| Voice AI | Gemini Native Audio | - | Live WebSocket audio | integrations/voice/ |
| Graph Persistence| AsyncPostgresSaver | - | LangGraph Checkpointing| orchestrator.py |
| Dashboard UI | React / Vite | ^19.2.8 | Copilot Admin Dashboard | frontend/package.json|
| Voice UI | Electron / React | ^19.2.8 | Phone Simulation Desktop | electron/package.json|
| Integrations | Telegram API | - | Text Chat Bot | integrations/telegram/|
| Infrastructure | Docker Compose | 3.8 | PG / Redis containers | docker-compose.yml |

*(Note: Redis is in docker-compose.yml, but the code does not actively use it for Pub/Sub or caching).*

---

## 4. Complete System Architecture

```text
       Demo App (Port 5173)
             │ (POST /events)
             ▼
    ┌─────────────────┐
    │  Copilot API    │ (Port 8000)
    │  (FastAPI)      │
    └─────────────────┘
             │ (Async Background Task)
             ▼
    ┌─────────────────┐
    │   LangGraph     │ (orchestrator.py)
    │   State Machine │
    └─────────────────┘
             │ (analyze_intent_node)
             ▼
    ┌─────────────────┐
    │  Intent Agent   │ (Gemini structured output)
    └─────────────────┘
             │ (sales_consultant_node)
             ▼
    ┌─────────────────┐
    │  Sales Agent    │ (Gemini with Tools)
    └─────────────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
  Electron      Telegram
  Trigger       Message
  (Port 3456)
      │
      ▼
  WebRTC Audio
  (Gemini Live)
```

---

## 5. Backend Architecture

- **Entry Point:** `backend/app/main.py`
- **Routers:** `events`, `whatsapp` (stubbed), `telegram`, `voice`, `dashboard`, `agents`, `system`.
- **Database:** PostgreSQL configured via `core/database.py`. Models track `CustomerSession`, `BehaviorEvent`, `IntentAssessment`, `AgentExecution`, `Conversation`, `CommerceAction`.
- **Flow:**
  1. API request hits `/api/v1/integration/events`.
  2. Data is written to `behavior_events` via SQLAlchemy.
  3. `BackgroundTasks` executes `process_event_background()`.
  4. Fetch all session events -> Trigger `run_copilot_graph()`.
  5. LangGraph executes state transition (Intent -> Sales).
  6. Graph state is checkpointed in PostgreSQL.
- **Middleware:** `RequestLoggingMiddleware` for tracing. CORS enabled globally.

---

## 6. Complete API Inventory

| Method | Endpoint | Purpose | Auth | Source File | Status |
|--------|----------|---------|------|-------------|--------|
| POST | `/api/v1/integration/events` | Ingest user events | No | `endpoints/events.py` | IMPLEMENTED |
| WS | `/api/v1/voice/stream` | Gemini Live Audio WebRTC | No | `endpoints/voice.py` | IMPLEMENTED |
| POST | `/api/v1/integrations/telegram/webhook` | Telegram messages | No | `endpoints/telegram.py`| IMPLEMENTED |
| GET | `/api/v1/dashboard/stats` | KPI metrics | Key | `endpoints/dashboard.py` | IMPLEMENTED |
| GET | `/api/v1/dashboard/sessions` | Active sessions list | Key | `endpoints/dashboard.py` | IMPLEMENTED |
| GET | `/api/v1/dashboard/sessions/{id}`| Session Customer 360 | Key | `endpoints/dashboard.py` | IMPLEMENTED |
| GET | `/api/v1/agents` | List AI Agent Configs | No | `endpoints/agents.py` | IMPLEMENTED |
| POST | `/api/v1/agents/{id}` | Update Agent Configs | No | `endpoints/agents.py` | IMPLEMENTED |
| POST | `/api/v1/system/keys` | Update .env API Keys | No | `endpoints/system.py` | IMPLEMENTED |

---

## 7. Database Architecture

**Database:** PostgreSQL (`COPILOT_DATABASE_URL`)
**ORM:** SQLAlchemy 2.0
**Migrations:** Alembic (`alembic_dir/versions/`)

### Core Models (`models.py`)
- `Customer`: `id`, `name`, `telegram_chat_id`.
- `CustomerSession`: `session_id`, `user_id`.
- `BehaviorEvent`: Immutable log (`session_id`, `event_type`, `event_metadata`).
- `IntentAssessment`: Outcome of LLM intent scoring (`intent_score`, `intent_category`).
- `AgentConfig`: Dynamic LLM configuration (`model_name`, `temperature`, `system_prompt`).
- `Conversation` & `ConversationMessage`: Chat/Transcript history.
- `CommerceAction`: Tool execution traces.

---

## 8. Event Ingestion System

Customer Activity (React) 
↓ (POST) 
`events.py` `/api/v1/integration/events`
↓ 
PostgreSQL (`behavior_events`, `customer_sessions` upsert)
↓ 
`BackgroundTasks` (`event_processor.py`)

- **Schema:** Requires `session_id`, `event_type`. Optional: `user_id`, `product_id`, `event_metadata`.
- **Idempotency:** None. Events are append-only.
- **Identification:** Maps `session_id` to `user_id` if provided. Upserts `Customer`.

---

## 9. Customer Intent System

**A. Rule-Based Intent Scoring:** **NOT IMPLEMENTED**
The intended architecture of calculating weights and thresholds (time spent, clicks, views) before waking the LLM agent does not exist. 

Instead, LangGraph triggers the `IntentAgent` (LLM) on **every** background event processor run.

**B. Intent Agent:** **IMPLEMENTED**
- **Trigger:** `analyze_intent_node` in LangGraph.
- **Input:** JSON dump of the entire event history for the session.
- **Reasoning:** Passed to Gemini LLM with Pydantic `IntentOutput`.
- **Output:** `intent_score`, `intent_category` (e.g. HIGH_PURCHASE_INTENT).
- **Persistence:** Written to `IntentAssessment` table.

---

## 10. Intent Agent

- **Model:** `gemini-1.5-flash` (configurable via DB).
- **Input:** `SystemPrompt` + `Customer Events: [{...}]`.
- **Output:** Structured JSON enforcing `IntentOutput` schema.
- **Tools:** None. Pure reasoning node.
- **State:** Alters `intent_score` and sets `should_intervene` boolean in GraphState.

---

## 11. LangGraph Architecture

- **StateGraph:** `GraphState` (session_id, events, intent_score, should_intervene, chat_history).
- **Nodes:** 
  1. `analyze_intent`: Calls IntentAgent, writes assessment.
  2. `sales_consultant`: Calls SalesConsultantAgent, triggers UI.
- **Routing:** `should_intervene_condition`. If True ➔ `sales_consultant`. If False ➔ `END`.
- **Checkpointer:** `AsyncPostgresSaver` utilizing the standard connection string.

```text
[START] -> analyze_intent -> [should_intervene?]
                               ├─(Yes)─> sales_consultant -> [END]
                               └─(No)──> [END]
```

---

## 12. Sales Consultant Agent

- **Model:** Gemini (configurable).
- **Tools:** `search_products`, `get_product_details`, `get_cart_status`, `add_product_to_cart`.
- **Action:** Bound tools via Langchain `bind_tools`.
- **Execution Loop:** Max 3 iterations to resolve tool calls.
- **Communication:** Triggers Electron UI (`http://127.0.0.1:3456/simulate`) OR replies directly to Telegram via HTTP provider.

---

## 13. Gemini Native Audio / Voice

- **Architecture:** WebSocket connection (`/api/v1/voice/stream`) forwards PCM chunks directly to Gemini.
- **Model:** `gemini-2.5-flash-native-audio-latest`.
- **Setup:** Uses `genai.Client.aio.live.connect` configuring `LiveConnectConfig` with Audio modality.
- **Voice:** Prebuilt voice `Puck`.
- **Tools:** Supports Commerce Agent tools via `FunctionDeclaration`.
- **Audio Trigger:** Sends a local `hello.pcm` to provoke the AI to speak first upon connection.
- **Status:** **IMPLEMENTED**

---

## 14. Electron Desktop Phone Simulation

- **Main Process (`main.js`):** Runs a hidden transparent window (`localhost:5180`). Starts local HTTP Server on Port 3456.
- **Trigger:** POST `/simulate` un-hides window and triggers IPC `incoming-call`.
- **React Renderer (`App.tsx`):**
  - Displays iOS-style incoming call UI.
  - Plays `ringtone.mp3`.
  - **Accept:** Opens `AudioContext` (24kHz playback, 16kHz capture). Connects WebSocket to Copilot backend.
  - **Capture:** `ScriptProcessorNode` extracts 16-bit PCM and sends to WS.
  - **Playback:** Decodes binary WebSocket blob into AudioBuffer.
- **Status:** **IMPLEMENTED**

---

## 15. Telegram Integration

- **Implementation:** `telegram/provider.py` & `endpoints/telegram.py`.
- **Status:** **IMPLEMENTED**
- **Flow:** 
  1. Telegram Webhook -> Backend.
  2. Links user to demo customer `cust_demo`.
  3. Creates `session_id`.
  4. Triggers LangGraph, bypassing intent (hardcoded `HIGH_PURCHASE_INTENT` and `should_intervene=True`).
  5. `sales_consultant_node` catches Telegram channel and executes `provider.send_text()`.

---

## 16. Frontend Dashboard

- **Status:** **IMPLEMENTED**
- **Pages:** `/` (Dashboard overview), `/agents` (Configuration).
- **Components:** `Customer360.tsx`, `KpiCard.tsx`, `AgentsConfigView.tsx`.
- **Customer 360:** Displays chat timeline, behavioral events, and fetches cart directly from Demo App backend (`http://localhost:8001/api/v1/cart`).
- **Data source:** Real PostgreSQL data, no mock data (except for Revenue approximation).

---

## 17. Real-Time System

- **Dashboard:** **POLLING** (`setInterval` every 3000ms inside `Customer360.tsx`).
- **Voice/Electron:** **WEBSOCKET** (Bi-directional raw PCM streaming).
- **Redis:** Configured in Docker but **NOT IMPLEMENTED** in code for Pub/Sub.

---

## 18. Communication Architecture

| Path | Protocol | Endpoint | Status |
|------|----------|----------|--------|
| Demo App ➔ Copilot | HTTP POST | `:8000/api/v1/integration/events` | IMPLEMENTED |
| Copilot ➔ Electron| HTTP POST | `127.0.0.1:3456/simulate` | IMPLEMENTED |
| Electron ➔ Copilot| WebSocket | `ws://:8000/api/v1/voice/stream` | IMPLEMENTED |
| Copilot ➔ Telegram| HTTP POST | `api.telegram.org/bot<token>` | IMPLEMENTED |
| Copilot ➔ Demo App| HTTP GET/POST| `http://localhost:8001/api/v1/...` | IMPLEMENTED |

---

## 19. Environment Configuration

| Variable | Purpose | Required | Used By |
|----------|---------|----------|---------|
| `GEMINI_API_KEY` | GenAI / Voice | Yes | Agents, Live Audio |
| `COPILOT_DATABASE_URL`| DB Connection | Yes | SQLAlchemy |
| `TELEGRAM_BOT_TOKEN`| Bot token | No | TelegramProvider |
| `VOICE_MODE` | real/demo toggle | No | VoiceProvider |
| `DASHBOARD_API_KEY` | Dashboard Auth | No | Dashboard API |

---

## 20. Docker / Infrastructure

**`docker-compose.yml` contents:**
- `postgres:15-alpine` (Port 5435) -> Persists `copilot_postgres_data`.
- `redis:7-alpine` (Port 6380) -> Persists `copilot_redis_data`.

*(Note: Application relies on local `.env` and `start.py` to run Python directly, not containerized).*

---

## 21. Testing

- **Framework:** `pytest`.
- **Files:** `test_llm.py`, `test_live_api.py`, `tests/test_api.py`.
- **Status:** Present but coverage unverified. Test execution scripts are manual.

---

## 22. Complete Current Data Flow

*(B) Product View ➔ LangGraph Pipeline*
```text
Customer Views Product 
  ➔ Demo App (tracker.ts) 
  ➔ Copilot (POST /events) 
  ➔ PostgreSQL (BehaviorEvent) 
  ➔ BackgroundTask (LangGraph) 
  ➔ IntentAgent (Evaluates Events) 
  ➔ If HIGH_INTENT ➔ SalesConsultantAgent 
  ➔ Trigger Electron UI.
```

*(K) Gemini Voice Flow*
```text
User Answers Electron App 
  ➔ Open Mic (16kHz PCM) 
  ➔ Copilot WS (/voice/stream) 
  ➔ Gemini Live API 
  ➔ LLM Speaks / Calls Tools 
  ➔ Copilot parses function calls 
  ➔ Executes against DemoApp (8001) 
  ➔ Returns tool result to Gemini 
  ➔ Gemini sends Audio blob 
  ➔ Copilot WS ➔ Electron Speaker (24kHz).
```

---

## 23. Security

- **Dashboard Auth:** Hardcoded `X-API-Key` interceptor via `verify_api_key`.
- **CORS:** Open (`allow_origins=["*"]`) in Copilot `main.py`.
- **Secrets:** Managed in `.env` securely.
- **Rate Limiting:** NOT IMPLEMENTED.
- **Webhook Security:** Telegram webhook lacks explicit signature validation in `telegram.py`.

---

## 24. Observability

- **Logging:** Standard Python `logging` module utilized.
- **Middleware:** `RequestLoggingMiddleware` exists.
- **DB Traces:** `AgentExecution` table designed to track trace IDs and latency (usage partial).

---

## 25. Current Status Matrix

| Feature | Status | Evidence/Source |
|---------|--------|-----------------|
| Event Ingestion | IMPLEMENTED | `events.py` |
| Event Storage | IMPLEMENTED | `behavior_events` table |
| Rule Scoring | NOT IMPLEMENTED | Pipeline goes straight to LLM |
| Intent Agent | IMPLEMENTED | `intent/agent.py` |
| LangGraph | IMPLEMENTED | `orchestrator.py` |
| PG Checkpointing| IMPLEMENTED | `AsyncPostgresSaver` |
| Sales Agent | IMPLEMENTED | `sales_consultant/agent.py` |
| Commerce Tools | IMPLEMENTED | `integrations/demo_app/client.py` |
| Gemini Voice | IMPLEMENTED | `voice/provider.py` |
| Electron App | IMPLEMENTED | `electron/src/App.tsx` |
| Telegram | IMPLEMENTED | `endpoints/telegram.py` |
| Dashboard | IMPLEMENTED | React Dashboard |
| Customer 360 | IMPLEMENTED | `Customer360.tsx` |
| Real-time UI | PARTIAL | Uses 3s polling, not WS |

---

## 26. DONE / PARTIAL / NOT DONE

**DONE**
- Agent state orchestration via LangGraph.
- LLM intent reasoning via Gemini structured output.
- WebRTC native audio streaming to Gemini Live API.
- Electron incoming call UI simulation.
- Telegram text fallback simulation.
- Dashboard configuration and session history viewing.
- Tool bindings for Copilot ➔ Demo App.

**PARTIALLY DONE**
- Customer 360 relies on HTTP polling.
- Telegram integration bypasses Intent scoring entirely.

**NOT DONE**
- Rule-based heuristics / thresholds to prevent LLM execution on every single minor event.
- Secure CORS boundaries.
- Redis pub/sub for real-time frontend updates.

---

## 27. KNOWN BUGS / RISKS

- **Event Spam:** LangGraph triggers a full LLM invocation (`IntentAgent`) on **every** background event. This is highly inefficient and expensive without a preceding rule-based threshold.
- **CORS & Hardcoded Ports:** `tracker.ts` in the Demo App hardcodes `localhost:8000`. The Copilot hardcodes `localhost:8001` for tool execution.
- **Voice Disconnects:** If Gemini API throws errors (e.g., 1000/1001 WS closures), the electron call might get abruptly terminated.

---

## 28. DEPENDENCIES BETWEEN COMPONENTS

```text
Demo App Tracker
      ↓
Copilot Event API
      ↓
PostgreSQL DB
      ↓
LangGraph Orchestrator
      ↓
Gemini LLM (Intent/Sales)
      ↓
Electron Trigger Server
      ↓
Electron WebRTC Audio
```

---

## 29. INTEGRATION CONTRACT WITH DEMO APP

**EXISTING CONTRACT:**
- **Inbound:** Copilot expects POST payloads at `/api/v1/integration/events` containing `session_id`, `event_type`.
- **Outbound:** Copilot executes tools against Demo App by hardcoding `http://localhost:8001/api/v1/...` for `/products/search`, `/products/{slug}`, `/cart`, and `/cart/items`.

**MISSING CONTRACT:**
- Copilot has no unified way of receiving async order confirmations or payment successes from the Demo App via webhooks.

---

## 30. FINAL ARCHITECTURE ASSESSMENT

**CURRENT ARCHITECTURE:** A highly decoupled, microservice-style orchestration engine utilizing LangGraph for intent validation and Gemini Live API for real-time voice synthesis.

**CURRENT IMPLEMENTATION STATUS:** The core "wow" factor (Voice calls, LangGraph, Tools) is fully implemented and functioning.

**BIGGEST GAPS:** The lack of rule-based event thresholds means the system relies purely on LLM reasoning for every mouse click, which is not scalable. Real-time UI updates rely on inefficient polling.

*Documentation generated from the current source code.*

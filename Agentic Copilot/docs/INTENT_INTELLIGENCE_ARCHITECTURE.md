# Intent Intelligence Architecture

## Overview
The Intent Intelligence pipeline replaces the synchronous per-event LLM evaluation with a deterministic rule-based engine. Events from the Demo App are ingested and scored in real-time. Only when the customer session terminates (explicitly or via idle timeout), and the score exceeds a threshold, is the Intent Agent invoked to generate a structured summary. This structured output will be used in future phases for the Sales Consultant Agent.

## Core Components

### 1. Event Tracking (Demo App)
The Demo App uses a fire-and-forget `tracker.ts` which sends behaviors to `/api/v1/integration/events`.
Supported behaviors:
- `PRODUCT_SEARCHED`
- `PRODUCT_VIEWED`
- `PRODUCT_DETAILS_VIEWED`
- `PRODUCT_IMAGE_VIEWED`
- `PRODUCT_SPECS_VIEWED`
- `PRODUCT_FEATURES_VIEWED`
- `PRODUCT_REVIEWS_VIEWED`
- `WISHLIST_ADDED`

The Demo App also sends a `SESSION_TERMINATED` event on `beforeunload` or explicit logout.

### 2. Event Ingestion (`events.py`)
Events are ingested synchronously into PostgreSQL (`BehaviorEvent`). During the same transaction, the Rule Engine (`scorer.py`) evaluates the event.

### 3. Rule-Based Scorer (`scorer.py`)
A deterministic engine that maintains anti-spam checks. It queries `IntentScoreHistory` to ensure a customer doesn't rack up infinite points for refreshing the same product page repeatedly.
If the score increases, it updates `CustomerSession.current_intent_score` and creates an `IntentScoreHistory` entry.

### 4. Session Finalization (`session.py` & `sweeper.py`)
Sessions are finalized via:
1. **Explicit Termination**: `POST /api/v1/integration/events/terminate`
2. **Idle Timeout**: A background sweeper (`sweeper.py`) runs every 60s looking for sessions inactive for > 1800s.

When a session finalizes, the engine:
- Marks the session as `TERMINATED`.
- Stops accepting new scores for it.
- If `current_intent_score >= threshold`, builds a structured payload and invokes the Intent Agent.

### 5. Intent Agent (`agent.py`)
Uses `gemini-2.5-flash` with Structured Output (JSON Schema) to analyze the full session payload.
It outputs:
- `intent_category`
- `confidence`
- `products_of_interest`
- `categories_of_interest`
- `reasoning`
- `recommended_action`
- `sales_consultant_context`

### 6. Logging (`intent_logger.py`)
Instead of overwhelming the stdout console, JSONL logs are stored in `/logs/intent/`:
- `intent_events.jsonl`: Every score change.
- `intent_sessions.jsonl`: Finalized sessions and their metadata.
- `intent_agent_inputs.jsonl`: Exact input sent to Gemini.
- `intent_agent_outputs.jsonl`: Exact structured JSON output from Gemini.

### 7. Dashboard Live Score
The React Dashboard `Customer360.tsx` polls `/api/v1/intent/{session_id}` every 3s to fetch the score and threshold, visualizing the progression in real-time. It explicitly shows if the Intent Agent triggered upon session termination.

# Current State of Intent Intelligence

This document outlines the **actual, verified current implementation** of the Intent Intelligence system in the Agentic Commerce Copilot. 

*Note: This documentation is based on strict code inspection of the existing codebase. No assumptions are made about intended or future behavior.*

---

## 1. PROJECT STRUCTURE

The following files and directories constitute the current actual implementation of the system:

```text
Demo App/
├── frontend/
│   ├── src/pages/ProductsPage.tsx
│   ├── src/pages/ProductDetailPage.tsx
│   ├── src/components/product/ProductCard.tsx
│   └── src/types/index.ts
└── backend/
    ├── app/api/v1/endpoints/events.py
    └── app/models/models.py

Agentic Copilot/
├── backend/
│   ├── app/api/v1/endpoints/events.py
│   ├── app/api/v1/endpoints/dashboard.py
│   ├── app/core/intent_logger.py
│   ├── app/models/models.py
│   ├── app/agents/intent/agent.py
│   └── app/services/intent_intelligence/
│       ├── scorer.py
│       ├── session.py
│       └── sweeper.py
│   ├── logs/intent/
│   └── tests/
│       └── test_intent_scorer.py
└── frontend/
    └── src/components/Customer360.tsx
```

---

## 2. CURRENT END-TO-END FLOW

1. **User Behavior**: User searches or clicks on products in the Demo App frontend.
2. **Event Generation**: The Demo App frontend (`trackEvent`) sends events to the Copilot backend (`POST /api/v1/events`).
3. **Event Ingestion**: `events.py` in the Copilot backend receives the event, upserts `CustomerSession` and `Customer`, and inserts a `BehaviorEvent`.
4. **Intent Scoring**: Synchronously, `process_event_for_intent` (`scorer.py`) evaluates the event, checks for spam/duplicates, and computes a `score_delta`.
5. **Session State**: The `session.current_intent_score` is updated in PostgreSQL. If `score >= session.intent_threshold`, `session.threshold_reached = True`.
6. **Logging**: The event and score change are logged to `intent_events_{session_id}.jsonl`.
7. **Session Termination**: 
   - *Idle Timeout*: A background task (`sweeper.py`) loops every 60 seconds and marks inactive sessions as `"TERMINATED"`.
   - *Explicit*: `POST /api/v1/events/terminate` forces termination.
8. **Intent Agent Invocation**: Inside `finalize_session` (`session.py`), if the score crossed the threshold, the session is summarized and passed to `IntentAgent.analyze_intent_structured()`.
9. **Intent Agent Output**: The output is generated and logged to `intent_agent_outputs_{session_id}.jsonl`. **(The Sales Consultant is NOT invoked).**
10. **Dashboard**: The frontend polls `GET /api/v1/dashboard/sessions` every 3 seconds to display real-time live intent scores.

---

## 3. DEMO APP EVENT TRACKING

| Event | Implemented? | Source File | Trigger | Payload | Backend Endpoint | Stored in DB? |
|------|------|------|------|------|------|------|
| `PRODUCT_SEARCHED` | ✅ IMPLEMENTED | `ProductsPage.tsx` | Search bar query | `metadata: { query }` | Copilot `POST /events` | Yes |
| `PRODUCT_VIEWED` | ✅ IMPLEMENTED | `ProductCard.tsx` | Click product | `product_id`, `category_id` | Copilot `POST /events` | Yes |
| `PRODUCT_VIEW_DURATION` | ✅ IMPLEMENTED | `ProductDetailPage.tsx` | Unmount / leave | `product_id`, `duration_seconds` | Copilot `POST /events` | Yes |
| `WISHLIST_ADDED` | ✅ IMPLEMENTED | `ProductCard.tsx`, `ProductDetailPage.tsx` | Heart click | `product_id`, `category_id` | Copilot `POST /events` | Yes |
| `PRODUCT_SPECS_VIEWED` | ❌ NOT IMPLEMENTED | - | - | - | - | No |
| `PRODUCT_FEATURES_VIEWED` | ❌ NOT IMPLEMENTED | - | - | - | - | No |
| `PRODUCT_REVIEWS_VIEWED` | ❌ NOT IMPLEMENTED | - | - | - | - | No |
| `SESSION_TERMINATED` | ❌ NOT IMPLEMENTED | - | - | - | - | No |

---

## 4. EVENT PAYLOADS

Actual schema expected by the Copilot Backend (`EventPayload`):

```json
{
  "event_type": "string",
  "session_id": "string",
  "user_id": "string (optional)",
  "product_id": "string (optional)",
  "category_id": "string (optional)",
  "order_id": "string (optional)",
  "event_metadata": {} 
}
```

---

## 5. EVENT INGESTION

- **Endpoint**: `POST /api/v1/events` (in `Agentic Copilot/backend/app/api/v1/endpoints/events.py`)
- **Validation**: Uses Pydantic `EventPayload`.
- **Database Operation**: 
  - Upserts `Customer` (if `user_name` exists in metadata).
  - Upserts `CustomerSession` and updates `last_active` timestamp.
  - Inserts `BehaviorEvent`.
- **Processing**: Synchronously awaits `process_event_for_intent` (commits after).

---

## 6. DATABASE MODELS

The following SQLAlchemy models **ACTUALLY EXIST** in `models.py`:

- `CustomerSession`: Tracks `session_id`, `current_intent_score`, `intent_threshold`, `threshold_reached`, `status`, `last_active`.
- `BehaviorEvent`: Tracks individual events (`event_type`, `product_id`, `metadata`).
- `IntentScoreHistory`: Tracks score changes (`previous_score`, `new_score`, `score_delta`, `signal`, `reason`).
- `IntentAssessment`: Stores final intent output.
- `Conversation`, `ConversationMessage`, `CommerceAction`, `AgentExecution`, `AgentConfig`.

---

## 7. RULE-BASED INTENT ENGINE

- **File**: `app/services/intent_intelligence/scorer.py`
- **Class/Function**: `process_event_for_intent`

**Current Implemented Rules:**

| Signal | Event | Weight | Conditions | Implemented? |
|------|------|------|------|------|
| `PRODUCT_SEARCHED` | Search | 5 | First time | ✅ IMPLEMENTED |
| `PRODUCT_VIEWED` | View | 5 | First time per product | ✅ IMPLEMENTED |
| `PRODUCT_VIEW_DURATION` | View Duration | 10 | First time per product | ✅ IMPLEMENTED |
| `WISHLIST_ADDED` | Wishlist | 15 | First time per product | ✅ IMPLEMENTED |
| `MULTIPLE_PRODUCT_VIEW` | 2nd Distinct View | 10 | 2 distinct products viewed | ✅ IMPLEMENTED |
| `PRODUCT_SPECS_VIEWED` | Specs | 8 | Defined, but no frontend trigger | 🟡 PARTIAL |
| `PRODUCT_FEATURES_VIEWED`| Features | 7 | Defined, but no frontend trigger | 🟡 PARTIAL |
| `PRODUCT_REVIEWS_VIEWED` | Reviews | 8 | Defined, but no frontend trigger | 🟡 PARTIAL |

*Anti-Spam*: Duplicate exact events on the same product result in `0` score delta.

---

## 8. LIVE INTENT SCORE

**Status: LIVE**
The score is calculated synchronously on every event ingestion in `events.py`. The score is persisted in PostgreSQL (`CustomerSession.current_intent_score`). It survives server restarts and correctly ignores duplicate exact events.

---

## 9. SESSION STATE

The `CustomerSession` model maintains the following fields:
- `session_id`
- `user_id`
- `last_active`
- `current_intent_score` (Float)
- `intent_threshold` (Float, defaults to 50.0)
- `threshold_reached` (Boolean)
- `status` (String, ACTIVE or TERMINATED)
- `finalized_at`

---

## 10. THRESHOLD BEHAVIOUR

When `current_intent_score >= intent_threshold`:
- The session `threshold_reached` boolean is set to `True`.
- **IMPORTANT**: Crossing the threshold does **NOT** immediately invoke the Intent Agent. The Intent Agent is only invoked during session termination.

---

## 11. SESSION TERMINATION

Session termination invokes the Intent Agent (if threshold was reached) and sets status to `TERMINATED`.
Implemented via:
1. **Explicit**: `POST /api/v1/events/terminate` calls `finalize_session`.
2. **Idle Sweeper**: A background task (`sweeper.py`) runs every 60 seconds. Any session inactive for > 5 minutes is passed to `finalize_session`.

---

## 12. INTENT AGENT

- **File**: `app/agents/intent/agent.py`
- **Class**: `IntentAgent`
- **When it is invoked**: ONLY inside `finalize_session()` in `session.py` (after termination).
- **Data it receives**: JSON summary object output from `build_session_summary()`.
- **Output**: Pydantic schema `IntentAgentOutput` representing final structured intelligence.

---

## 13. INTENT AGENT INPUT

The `build_session_summary` function in `session.py` maps the database to this schema for the LLM:

```json
{
  "session_id": "string",
  "customer_id": "string",
  "session": { "duration_seconds": 0 },
  "intent_score": {
    "final_score": 0.0,
    "threshold": 50.0,
    "threshold_reached": true
  },
  "searches": ["list of strings"],
  "products_viewed": [{"product_id": "str", "view_count": 0}],
  "behaviour_signals": {
    "specifications_viewed": false,
    "features_viewed": false,
    "reviews_viewed": false,
    "multiple_products_viewed": false
  },
  "wishlist_products": ["list of strings"],
  "score_breakdown": [{"signal": "str", "score": 0.0, "reason": "str"}]
}
```

---

## 14. INTENT AGENT OUTPUT

The output strictly follows Pydantic structured schemas. It outputs:
- `intent_category` (HIGH_PURCHASE_INTENT, EXPLORATORY, SUPPORT, CHURN_RISK, UNKNOWN)
- `confidence`
- `reasoning`
- `customer_interest`
- `recommended_action`
- `sales_consultant_context`

---

## 15. SALES CONSULTANT HANDOFF

**Status: ❌ NOT IMPLEMENTED**
The Sales Consultant is completely decoupled. The intent agent output is successfully generated and logged, but it is explicitly not passed downstream.

Actual code from `session.py`:
```python
logger.info("INTENT_AGENT_OUTPUT_READY_FOR_SALES_CONSULTANT")
logger.info("SALES_CONSULTANT_CALLED = false. Payload logged to intent_agent_outputs.jsonl")
```

---

## 16. LOGGING

Logs are written locally via `IntentLogger` (`app/core/intent_logger.py`). They are separated by session ID:
- `logs/intent/intent_events_{session_id}.jsonl`
- `logs/intent/intent_agent_inputs_{session_id}.jsonl`
- `logs/intent/intent_agent_outputs_{session_id}.jsonl`
- `logs/intent/intent_sessions_{session_id}.jsonl`

---

## 17. DASHBOARD

The Dashboard (`Customer 360`) pulls data from `GET /api/v1/dashboard/sessions` and `GET /api/v1/dashboard/sessions/{session_id}`.
It correctly maps and displays:
- Real-time `current_intent_score` vs `threshold`.
- `threshold_reached` status.
- Session status (`ACTIVE` vs `TERMINATED`).
- `is_active` color-coded dots.

---

## 18. APIs

| Method | Endpoint | Purpose | Implemented | Used By |
|------|------|------|------|------|
| `POST` | `/api/v1/events` | Event Ingestion | ✅ | Demo App |
| `POST` | `/api/v1/events/terminate` | Explicit Termination | ✅ | Demo App / Tools |
| `GET` | `/api/v1/dashboard/sessions` | List sessions | ✅ | Agentic Copilot Frontend |
| `GET` | `/api/v1/dashboard/sessions/{id}`| Customer 360 Detail | ✅ | Agentic Copilot Frontend |

---

## 19. CONFIGURATION

- `INTENT_THRESHOLD` / Gemini Configuration / Database URL are present in `.env`.

---

## 20. LANGGRAPH

**Status: ❌ NOT INTEGRATED**
The Intent Intelligence pipeline currently runs completely standalone. It is directly executed inside `session.py` via standard async function calls, entirely bypassing any existing LangGraph nodes.

---

## 21. TESTS

**Status: ⚠️ IMPLEMENTED BUT NOT VERIFIED**
There is a single test file `tests/test_intent_scorer.py`. It contains a placeholder skeleton using `pytest.mark.asyncio`, but currently does not contain actual functional integration test assertions. 

---

## 22. ACTUAL RUNTIME VERIFICATION

Runtime verification was successful. Terminal logs confirm that the sweeping loop successfully tracks idle sessions and triggers the LLM as expected.

---

## 24. FINAL STATUS MATRIX

| Component | Status | Evidence | Notes |
|------|------|------|------|
| Demo App Tracking | 🟡 PARTIAL | `ProductCard.tsx` | Views/Wishlists work. Specs/Reviews missing. |
| Event Ingestion | ✅ IMPLEMENTED | `events.py` | Upserts DB properly. |
| PostgreSQL Persistence | ✅ IMPLEMENTED | `models.py` | Fully mapped and saving. |
| Rule Engine | ✅ IMPLEMENTED | `scorer.py` | Accurately assigns weights and stops duplicates. |
| Live Scoring | ✅ IMPLEMENTED | `scorer.py` | Syncs cleanly with frontend dashboard. |
| Threshold Logic | ✅ IMPLEMENTED | `scorer.py` | Flags threshold accurately without invoking LLM prematurely. |
| Session Termination | ✅ IMPLEMENTED | `session.py`, `sweeper.py` | Handled properly via explicit API or idle timeout. |
| Intent Agent | ✅ IMPLEMENTED | `agent.py` | Successfully receives structured data and outputs reasoning. |
| Agent Logging | ✅ IMPLEMENTED | `intent_logger.py` | Session-specific `.jsonl` logging is active. |
| LangGraph | ❌ NOT IMPLEMENTED | `session.py` | No LangGraph integration yet. |
| Sales Consultant | ❌ NOT IMPLEMENTED | `session.py` | Explicitly skipped via logs. |
| Tests | 🟡 PARTIAL | `test_intent_scorer.py` | Empty placeholder tests exist. |

---

## 25. CONCLUSION

### WHAT IS ACTUALLY WORKING RIGHT NOW
The end-to-end event ingestion, live score calculation, anti-spam protections, dashboard visibility, background session idle timeout, and the actual Intent Agent LLM structured output generation are fully functional.

### WHAT IS NOT WORKING / MISSING
1. **Frontend Event Gaps:** Features viewed, Specs viewed, and Reviews viewed are missing in the Demo App.
2. **Sales Consultant Handoff:** The Intent Agent successfully generates highly detailed context but drops it onto the floor instead of triggering the Sales Consultant.
3. **LangGraph Pipeline:** The Intent Agent runs as a standalone Python class, rather than a compiled node inside LangGraph.

### WHAT NEEDS TO BE DONE NEXT

**P0 (Critical for functional architecture)**
- Implement the handoff pipeline so the Intent Agent's `sales_consultant_context` output triggers a message/notification to the Sales Consultant.

**P1 (Production Readiness)**
- Implement LangGraph integration to ensure the intent agent runs natively within the graph framework.
- Implement proper testing fixtures in `test_intent_scorer.py`.

**P2 (Improvements)**
- Implement the missing frontend trackers (`PRODUCT_SPECS_VIEWED`, `PRODUCT_FEATURES_VIEWED`, `PRODUCT_REVIEWS_VIEWED`).

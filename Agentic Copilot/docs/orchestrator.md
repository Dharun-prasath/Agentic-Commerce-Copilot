# Orchestrator

The Orchestrator is the central nervous system of the Agentic Commerce Copilot. It is purely deterministic (rule-based) and handles the routing of events between AI Agents, Execution Engines, and the internal Database.

## Core Responsibilities

1. **Event Consumption**: Listens for termination of customer sessions or intent triggers.
2. **Agent Routing**: Decides which AI Agent (Intent, Product Intelligence, Sales Consultant) needs to run next based on the `OrchestratorJob` state.
3. **Engine Routing**: Dispatches asynchronous tasks to the Telegram Engine and synchronous requests to the Commerce Engine.
4. **State Management**: Maintains a durable state machine using the `OrchestratorJob` and `CustomerSession` tables in PostgreSQL.

## The Execution Flow

The Orchestrator relies on a `QueueManager` to reliably process background jobs.

1. **Threshold Trigger**: When a `CustomerSession` ends, the Orchestrator compares the `current_intent_score` against the `intent_threshold`.
2. **Intent Agent Trigger**: If the threshold is met, it transitions the `OrchestratorJob` to `QUEUED`. The `QueueManager` picks this up and executes the `IntentAgent`.
3. **Sales Consultant Trigger**: After the Intent Agent generates an `IntentAssessment`, the Orchestrator calls an external local service (`http://127.0.0.1:3456/simulate`) to trigger the Electron-based voice app, which initiates the `SalesConsultantAgent`.
4. **Product Intelligence Loop**: When the Sales Consultant gathers requirements, it calls a tool that hits the Orchestrator's internal API (`/api/v1/internal/product-intelligence`). The Orchestrator spins up the `ProductIntelligenceAgent` asynchronously.
5. **Telegram Trigger**: Once Product Intelligence yields recommendations, the Orchestrator spins up a background task to push these recommendations through the `TelegramEngine`.

## Important Files

- `app/services/orchestrator/service.py`: Contains the `OrchestratorService` class, defining the state machine transitions and routing logic.
- `app/services/orchestrator/queue_manager.py`: Implements a singleton background worker that reliably dequeues and executes `IntentAgentJob` records with retry logic.

## Error Handling & Retries

- The `QueueManager` implements an atomic lease mechanism (`lease_until`) to prevent concurrent execution of the same job.
- Jobs have a `max_attempts` limit (default 3). If an agent fails, the error is recorded, and the job is retried until `max_attempts` is reached, at which point it is marked as `FAILED`.

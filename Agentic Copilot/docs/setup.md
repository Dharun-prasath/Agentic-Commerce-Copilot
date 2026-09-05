# Setup & Configuration

## Environment Variables

The Agentic Copilot backend requires an `.env` file in the `Agentic Copilot/backend` directory.

```env
# Server
PORT=8080
ENVIRONMENT=development

# Database
# This is the copilot's own internal database for tracking Orchestrator state and Events
DATABASE_URL=sqlite+aiosqlite:///./copilot.db

# External Integrations
# The URL of the Demo App
DEMO_APP_API_URL=http://localhost:8000/api/v1
DEMO_APP_BASE_URL=http://localhost:5174
# The actual Postgres database of the Demo App for direct writes
COMMERCE_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/demo_db

# AI Models
LLM_MODEL=gemini-1.5-flash
INTENT_AGENT_MODEL=gemini-1.5-pro
PRODUCT_AGENT_MODEL=gemini-1.5-flash
# The Sales Consultant relies on native audio and ignores these strings

# Credentials
GEMINI_API_KEY=your-gemini-key
TELEGRAM_BOT_TOKEN=your-bot-token
```

## Running the Copilot

There are provided launch scripts at the root of the `Agentic Copilot` project.

### 1. The Backend
This script launches the FastAPI server (which includes the Orchestrator, QueueManager, and API endpoints).

```bash
cd "Agentic-Commerce-Copilot/Agentic Copilot"
python3 start.py
```

### 2. The Electron UI (Voice Bridge)
This script launches a Vite/React frontend wrapped in Electron, which serves as the "Phone UI" to connect to the Gemini Live API over WebSockets.

```bash
cd "Agentic-Commerce-Copilot/Agentic Copilot"
python3 start_electron.py
```

*Note: Ensure the Demo App is already running, as the Copilot depends on it for catalog lookups and commerce execution.*

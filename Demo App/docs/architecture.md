# Demo Commerce Architecture

## High-Level Design

The Demo Commerce Application follows a modern, decoupled web architecture comprising a headless backend API and a standalone frontend client.

### 1. Backend (FastAPI + PostgreSQL)

The backend is built with **FastAPI**, an asynchronous, high-performance web framework for Python.

- **Routing & Endpoints**: API routes are organized by domain in `app/api/v1/endpoints` (e.g., `cart.py`, `commerce.py`, `products.py`).
- **Services**: Business logic is encapsulated in the `app/services/` layer (e.g., `product_service.py`, `checkout_service.py`).
- **Data Access (Repositories)**: The database is accessed via SQLAlchemy ORM.
- **Models**: Defines the precise structure of the relational tables (see `models.py`).
- **Schemas**: Pydantic models in `app/schemas/` ensure data validation and precise serialization of JSON requests/responses.

### 2. Frontend (React + Vite)

The frontend is a **React 19** application, built using **Vite** for rapid bundling and hot-module replacement.

- **Component Library**: Utilizes Radix UI for accessible base components.
- **Styling**: Tailwind CSS is used for rapid, utility-first styling.
- **Routing**: React Router handles client-side navigation.
- **State Management**: 
  - `zustand` is used for global client state (e.g., the Cart state, UI toggles).
  - `TanStack React Query` is used for fetching, caching, and synchronizing server state.
- **Integrations**: Razorpay's checkout script is injected to handle payment flows.

### 3. Agentic Copilot Integration Points

The Demo App is architected specifically to support the Agentic Commerce Copilot. 

- **Telemetry**: The frontend tracks user events (e.g., `VIEW_PRODUCT`, `SEARCH`) and pushes them to the backend `/api/v1/events` endpoint.
- **Event Storage**: The backend stores these as immutable `Event` records in PostgreSQL.
- **Commerce APIs**: The Copilot (running as a separate service) queries the `/api/v1/commerce/` routes to interact with the catalog and manage user carts deterministically, effectively bypassing the frontend UI to act on the user's behalf.

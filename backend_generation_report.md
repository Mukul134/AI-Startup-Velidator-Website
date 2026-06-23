# AI Startup Validator: FastAPI Backend Specification

This document details the completed production-ready FastAPI backend architecture generated for the **AI Startup Validator** platform under the `backend/` directory.

---

## 1. Directory Structure

The codebase is organized following **Clean Architecture** patterns, separating routing, business logic, data models, and agent tasks:

```text
backend/
├── main.py                   # FastAPI Application Entrypoint
├── requirements.txt          # Package dependencies
├── .env.example              # Configuration environment template
└── app/
    ├── config.py             # Configuration parsing & settings (Pydantic BaseSettings)
    ├── database.py           # SQLAlchemy Async Engine, sessions, and DB initializer
    ├── agents/               # LangGraph components (State, Nodes, Graph compilation)
    ├── models/               # SQLModel Database entity declarations
    ├── schemas/              # Pydantic validation definitions for requests/responses
    ├── repositories/         # Database access abstraction layers
    ├── services/             # Core business processes (Auth, Validation workflow trigger)
    └── routers/              # API controllers & route definitions
```

---

## 2. Implemented Components

All files have been written directly to the project folder at [E:\AI Startup\backend](file:///E:/AI%20Startup/backend).

### A. Configurations & DB Context
*   **Settings Controller (`app/config.py`):** Automatically parses environment configurations from `.env` using `pydantic-settings` to guarantee validated typing of credentials on start.
*   **Async Connection Pool (`app/database.py`):** Uses an asynchronous connection pool (`asyncpg` driver) with SQLAlchemy's `create_async_engine` to perform fully async non-blocking queries.

### B. Data & Validation Schemas
*   **Unified DB Schema (`app/models/entities.py`):** Groups the PostgreSQL tables (`User`, `StartupProject`, `Report`, `CompetitorAnalysis`, `CustomerPersona`, `InvestorReview`, `RiskAssessment`, `RevenuePrediction`) into a single file to cleanly handle bidirectional circular relationships in SQLModel.
*   **Request & Response schemas (`app/schemas/project.py`):** Manages inbound validation limits (e.g. constraints on budget value and text length) and output schemas to clean up API payloads.

### C. Services & Routing Layers
*   **Supabase JWT Verification (`app/services/auth.py`):** Exposes `get_current_user` dependency. Validates the `Authorization: Bearer <JWT>` header using HS256 algorithm with Supabase's signature secret. Contains auto-profile generation fallback if public schema triggers have lag.
*   **Workflow Runner (`app/services/project.py`):** Schedules the validation runner inside a FastAPI `BackgroundTask`. It calls the LangGraph compiler (`app_workflow.ainvoke`), maps the outputs, writes details across all database sub-tables, and updates run statuses.
*   **Projects API Router (`app/routers/projects.py`):** Routes traffic for `/projects/` endpoints:
    *   `POST /projects/`: Submits project validation brief (returns `202 Accepted` immediately).
    *   `GET /projects/`: Returns history logs for the user.
    *   `GET /projects/{id}/`: Fetches run state.
    *   `GET /projects/{id}/report`: Returns full aggregated sub-agent report metrics once complete.

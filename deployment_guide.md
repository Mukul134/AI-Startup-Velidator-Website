# AI Startup Validator: Production Deployment Guide

This guide details the steps to build, configure, secure, and deploy the AI Startup Validator platform using **Supabase** (Database), **Railway** (FastAPI Backend), and **Vercel** (Next.js Frontend).

---

## 1. Environment Variable Specifications

To ensure database and model services operate securely, establish the following parameters across your host providers:

### A. Database (Supabase Settings)
No actions needed; config values are generated on Supabase project creation.

### B. FastAPI Backend (Railway Variables)
Add these environment variables under the "Variables" tab in your Railway service settings:
*   `DATABASE_URL`: Connection string. Ensure it uses `postgresql://` (FastAPI translates this to async `postgresql+asyncpg://` automatically).
*   `SUPABASE_URL`: Public API URL (e.g. `https://[project-id].supabase.co`).
*   `SUPABASE_SERVICE_KEY`: Service role secret API key (required to bypass Row Level Security inside the background agent validation worker).
*   `SUPABASE_JWT_SECRET`: API JWT secret used to decode client tokens locally.
*   `OPENAI_API_KEY`: Model provider key (e.g. `sk-proj-...`).
*   `ANTHROPIC_API_KEY` (Optional): Fallback model key.
*   `ALLOWED_ORIGINS`: JSON array of CORS origins: `["https://your-vercel-domain.vercel.app"]`.
*   `DEBUG`: Set to `False` in production.

### C. Next.js Frontend (Vercel Variables)
Configure these variables inside your Vercel Project Dashboard:
*   `NEXT_PUBLIC_SUPABASE_URL`: Public API URL of your Supabase instance.
*   `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase client-safe anon key.
*   `NEXT_PUBLIC_API_URL`: The domain URL of your backend Railway service (e.g., `https://ai-startup-backend.up.railway.app`).

---

## 2. Docker Architecture Configuration

The backend is configured to use a premium, secure multi-stage Docker build structure. 
Refer to the created [Dockerfile](file:///E:/AI%20Startup/backend/Dockerfile) for details.

### Security Highlights:
1.  **Multi-stage builder:** Prevents build tools (`build-essential`, header dependencies) from expanding container image size in the final step.
2.  **Runner limits:** Uses python-slim, copies compiled packages, and executes as non-root `appuser` (UID `10001`) to protect host servers against execution escapes.
3.  **Active healthchecks:** Integrates a health-probe command (`curl -f http://localhost:8000/health`) executing every 30 seconds to support blue/green deployments and self-healing.

---

## 3. GitHub Actions CI/CD Pipeline

The deployment pipeline is automated using GitHub Actions. Refer to the created [deploy.yml](file:///E:/AI%20Startup/.github/workflows/deploy.yml) workflow for configurations.

### Key Deployment Secrets:
Add the following secrets to your GitHub repository under `Settings -> Secrets and variables -> Actions`:
*   `SUPABASE_PROJECT_ID`: Supabase project reference ID.
*   `SUPABASE_DB_PASSWORD`: Password for your Supabase PostgreSQL database.
*   `SUPABASE_ACCESS_TOKEN`: API developer access token for CLI operations.
*   `RAILWAY_TOKEN`: Access token generated from your Railway account settings.
*   `VERCEL_TOKEN`: Vercel personal access token.

---

## 4. Production Monitoring & Logging

### A. Logging Best Practices
*   **FastAPI Logs:** Standardized under Uvicorn's JSON formatter inside Railway. Uvicorn outputs are automatically captured by Railway and can be streamed to central log aggregators:
    *   Set logging levels inside Railway variables: `LOG_LEVEL=info`.
    *   Do not write logs to local server files (Docker containers are ephemeral). Stream straight to stdout/stderr.
*   **Log Drains:** Set up a log drain on Railway pointing to **Logflare**, **Datadog**, or **BetterStack** to search for error responses or trace agent latency metrics.

### B. Health & Performance Monitoring
*   **Uptime Probes:** Set up ping probes pointing to `https://your-backend.up.railway.app/health` and your frontend domain using **UptimeRobot** or **BetterStack Uptime** (interval: 1 minute).
*   **Database Statistics:** Supabase provides graphical CPU, disk, memory, and active pool transaction metrics directly inside the Supabase Project Dashboard under `Monitor -> API Usage`.
*   **Frontend Web Vitals:** Enable Vercel Web Vitals directly on your project to track core rendering parameters, user experience delays, and browser exceptions.
*   **Agent Profiling (LangSmith):** If you are running complex multi-agent iterations, enable LangSmith tracking on the backend for visual debugging of LLM prompts:
    *   Railway variables: `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY=your-langchain-key`.

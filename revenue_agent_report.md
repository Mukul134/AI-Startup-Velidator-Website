# AI Startup Validator: Revenue Prediction Agent Spec

This document details the code design, Pydantic constraints, and operational logic of the **Revenue Prediction Agent** configured to generate 3-year recurring financial forecasts.

---

## 1. Code Placement
The production-grade Python script has been written directly to the project at:
*   [revenue_prediction.py](file:///E:/AI%20Startup/backend/app/agents/nodes/revenue_prediction.py)

---

## 2. Agent Workflow Mechanics

```mermaid
graph TD
    Start[State Input] --> RunNode[revenue_prediction_node]
    
    subgraph Execution Loop
        RunNode --> LoadContext[Load market_data, competitor_data, customer_data]
        LoadContext --> CheckKeys{API Keys Available?}
        CheckKeys -->|No| MockRun[Load mock 3-year projection arrays]
        CheckKeys -->|Yes| LLMRun[Compile ChatPromptTemplate]
        
        LLMRun --> Bind[Bind structured_output: RevenuePredictionOutput]
        Bind --> Invoke[Invoke GPT-4o]
        
        Invoke -->|Network/429 Exception| Tenacity{Tenacity Retry < 3?}
        Tenacity -->|Yes| RetryWait[Exponential Backoff Wait]
        RetryWait --> Invoke
        Tenacity -->|No| Crash[Throw ParseException]
    end

    MockRun --> Map[Map/Transform projections to DB schema formatting]
    Invoke -->|Success JSON| Map
    Crash --> Fallback[Load default zeroed projections & logs error to state['errors']]
    
    Fallback --> Map
    Map --> UpdateState[Save forecast to state['revenue_data'] and breakeven to state['revenue_metadata']]
    UpdateState --> End[Return State Dictionary]
```

---

## 3. Key Design Features

### A. Dynamic Financial Sizing Model (`RevenuePredictionOutput`)
Directs GPT-4o to construct mathematical financial models containing:
*   **Yearly Projections (`YearlyForecastDetail`):**
    *   `year` (1, 2, or 3)
    *   `mrr` (projected Month-End recurring revenue)
    *   `arr` (projected Annual recurring revenue)
    *   `projected_revenue` (total generated revenue)
    *   `projected_growth_rate` (percentage change)
    *   `assumptions` (pricing tier calculations, customer caps, conversion rate percentages)
*   **Profitability Metrics:**
    *   `months_to_breakeven` (numeric months)
    *   `breakeven_explanation` (operating costs and unit economics analysis)

### B. Database Schema Adaptation Layer
To ensure the DB fields match the SQLModel tables without losing MRR/ARR details:
*   Appends MRR and ARR indicators as structured notes inside the `assumptions` list. This keeps database schemas clean while transferring metrics to reports.
*   Extracts the lists of `yearly_forecasts` into `revenue_data`.
*   Saves the `months_to_breakeven` and explanation under `revenue_metadata` in the state, making it readable for the `Report Agent`.

### C. Tenacity and Node Safety
*   **Error Catching:** Logs tracebacks and saves them to `state["errors"]["revenue_prediction"]`.
*   **Degraded State:** Fallback loads a default year 1 projection with a warning note to let evaluations continue safely if API calls fail.
*   **Logical Cohesion:** Sets a low temperature (`0.1`) to ensure mathematical alignment (e.g., Year-End MRR * 12 roughly matches ARR).

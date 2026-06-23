# AI Startup Validator: Investor Agent Spec

This document details the code design, Pydantic constraints, and operational logic of the **Investor Agent** configured to act as a Venture Capital partner.

---

## 1. Code Placement
The production-grade Python script has been written directly to the project at:
*   [investor_agent.py](file:///E:/AI%20Startup/backend/app/agents/nodes/investor_agent.py)

---

## 2. Agent Workflow Mechanics

```mermaid
graph TD
    Start[State Input] --> RunNode[investor_agent_node]
    
    subgraph Execution Loop
        RunNode --> LoadContext[Load market_data, competitor_data, revenue_data]
        LoadContext --> CheckKeys{API Keys Available?}
        CheckKeys -->|No| MockRun[Load mock partner review list]
        CheckKeys -->|Yes| LLMRun[Compile ChatPromptTemplate]
        
        LLMRun --> Bind[Bind structured_output: InvestorAgentOutput]
        Bind --> Invoke[Invoke GPT-4o]
        
        Invoke -->|Network/429 Exception| Tenacity{Tenacity Retry < 3?}
        Tenacity -->|Yes| RetryWait[Exponential Backoff Wait]
        RetryWait --> Invoke
        Tenacity -->|No| Crash[Throw ParseException]
    end

    MockRun --> Map[Map/Transform score scale & compile markdown details]
    Invoke -->|Success JSON| Map
    Crash --> Fallback[Load zeroed safety reviews & logs error to state['errors']]
    
    Fallback --> Map
    Map --> UpdateState[Save list to state['investor_data']]
    UpdateState --> End[Return State Dictionary]
```

---

## 3. Key Design Features

### A. Structured VC Review Model (`InvestorPartnerReview`)
Prompts GPT-4o to act as a VC general partner, evaluating the business along five key dimensions:
*   **Market Opportunity:** Sizing, CAGR, headwinds/tailwinds check.
*   **Business Model:** LTV margins and distribution scalability.
*   **Competition:** Pricing comparison and market positioning.
*   **Defensibility:** Moats, network effects, or barriers.
*   **Founder & Execution Risk:** Capital efficiency risks.

Produces a verdict (`invest` | `watch` | `pass`), list of strengths, list of weaknesses, and a score out of 10.

### B. Database Schema Compatibility Mapper
Bridges the VC scoring and detail models to our database repository shape:
1.  **Feedback Compiler:** Merges the five analysis text fields, strengths list, and weaknesses list into a single structured Markdown text string stored in `feedback_details`.
2.  **Venture Score Translation:** Converts the `score_out_of_10` (integer between 1 and 10) to the database's `investment_score` representation (0 to 100 percentage scale) by multiplying by 10.

### C. Tenacity and Node Safety
*   **Connection Resilience:** Applies retry patterns (3 attempts) to resolve temporary API timeout blocks.
*   **Safe Recoveries:** In the event of persistent errors, logs details to `state["errors"]["investor_agent"]` and loads a pass-verdict placeholder to ensure compilation nodes succeed.
*   **Analytical Control:** Uses a low temperature setting (`0.1`) to ensure highly analytical, risk-averse investment evaluations.

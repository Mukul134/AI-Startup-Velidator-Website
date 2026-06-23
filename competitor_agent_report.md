# AI Startup Validator: Competitor Analysis Agent Implementation Spec

This document details the code capabilities, data structures, and implementation logic of the **Competitor Analysis Agent** in the multi-agent system.

---

## 1. Code Placement
The production-grade Python script has been written directly to the project at:
*   [competitor_analysis.py](file:///E:/AI%20Startup/backend/app/agents/nodes/competitor_analysis.py)

---

## 2. Agent Workflow Mechanics

```mermaid
graph TD
    Start[State Input] --> RunNode[competitor_analysis_node]
    
    subgraph Execution Loop
        RunNode --> LoadMarket[Load state['market_data']]
        LoadMarket --> CheckKeys{API Keys Available?}
        CheckKeys -->|No| MockRun[Load Mock Competitors List]
        CheckKeys -->|Yes| LLMRun[Compile ChatPromptTemplate]
        
        LLMRun --> Bind[Bind structured_output: CompetitorAnalysisOutput]
        Bind --> Invoke[Invoke GPT-4o]
        
        Invoke -->|Network/429 Exception| Tenacity{Tenacity Retry < 3?}
        Tenacity -->|Yes| RetryWait[Exponential Backoff Wait]
        RetryWait --> Invoke
        Tenacity -->|No| Crash[Throw ParseException]
    end

    MockRun --> UpdateState[Save list to state['competitor_data']]
    Crash --> Fallback[Load default data structure & logs error to state['errors']]
    Invoke -->|Success JSON| UpdateState
    Fallback --> UpdateState
    
    UpdateState --> End[Return State Dictionary]
```

---

## 3. Key Design Features

### A. Deep Competitive Sizing (`CompetitorDetail`)
Uses structured output binding to force GPT-4o to identify top players and output detailed records containing:
*   `competitor_name`
*   `market_share` (float percentage)
*   `pricing_model` (subscription/freemium detail)
*   `key_features` (product functionality bullets)
*   `market_positioning` (value proposition angle)
*   `strengths`, `weaknesses`, `opportunities`, `threats` (SWOT analysis arrays)
*   `threat_level` (low | medium | high | critical)

### B. Tenacity Automation & Graceful Safety
*   **Tenacity Protection:** Implements identical backoff parameters (3 attempts) to resolve temporary API timeout blockages.
*   **Safety Defaulting:** If execution fails, injects a placeholder structured competitor object so downstream evaluation nodes (like the `Risk Agent`) can query fields without causing dictionary key errors.
*   **State Integration:** Automatically registers errors in `state["errors"]["competitor_analysis"]` for visibility during run checks.

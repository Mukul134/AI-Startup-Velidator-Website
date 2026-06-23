# AI Startup Validator: Customer Persona Agent Implementation Spec

This document details the code capabilities, data structures, and implementation logic of the **Customer Persona Agent** in the multi-agent system.

---

## 1. Code Placement
The production-grade Python script has been written directly to the project at:
*   [customer_persona.py](file:///E:/AI%20Startup/backend/app/agents/nodes/customer_persona.py)

---

## 2. Agent Workflow Mechanics

```mermaid
graph TD
    Start[State Input] --> RunNode[customer_persona_node]
    
    subgraph Execution Loop
        RunNode --> LoadMarket[Load state['market_data']]
        LoadMarket --> CheckKeys{API Keys Available?}
        CheckKeys -->|No| MockRun[Generate exactly 10 mock profiles]
        CheckKeys -->|Yes| LLMRun[Compile ChatPromptTemplate]
        
        LLMRun --> Bind[Bind structured_output: CustomerPersonaOutput]
        Bind --> Invoke[Invoke GPT-4o]
        
        Invoke -->|Network/429 Exception| Tenacity{Tenacity Retry < 3?}
        Tenacity -->|Yes| RetryWait[Exponential Backoff Wait]
        RetryWait --> Invoke
        Tenacity -->|No| Crash[Throw ParseException]
    end

    MockRun --> Map[Map/Transform fields to DB schema shape]
    Invoke -->|Success JSON| Map
    Crash --> Fallback[Load fallback persona arrays & logs error to state['errors']]
    
    Fallback --> Map
    Map --> UpdateState[Save list to state['customer_data']]
    UpdateState --> End[Return State Dictionary]
```

---

## 3. Key Design Features

### A. Strict Persona Sizing (`CustomerPersonaOutput`)
Uses structured output binding to force GPT-4o to generate **exactly 10 customer personas** using properties specified by the user:
*   `name`
*   `age`
*   `occupation`
*   `pain_points` (array)
*   `buying_power` (Low/Medium/High)
*   `willingness_to_pay` (price sensitivity details)

### B. Dynamic DB-Schema Mapper
To bridge the gap between user requirements and database structures without complicating SQL code:
*   Maps `name` to the database schema's `persona_name` field.
*   Packs `age`, `occupation`, and `buying_power` into the database's `demographics` JSONB dictionary.
*   Passes `pain_points` directly.
*   Formats `willingness_to_pay` as a string descriptor and stores it in the database's `buying_behavior` field.

### C. Tenacity Reliability and Safety
*   **Tenacity Integration:** Protects execution flow against transient API call drops (3 retry attempts).
*   **Workflow Fallback:** In the event of persistent errors, loads a fallback persona row to satisfy downstream code logic (like investor evaluate modules) and records the traceback exception in `state["errors"]["customer_persona"]`.
*   **High Diversity Temperature:** Uses a temperature setting of `0.25` to balance analytical compliance with rich diversity in demographics and occupations.

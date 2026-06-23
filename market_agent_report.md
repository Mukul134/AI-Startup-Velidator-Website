# AI Startup Validator: Market Research Agent Implementation Spec

This document outlines the detailed architecture and code capabilities of the **Market Research Agent** implemented inside the multi-agent validator platform.

---

## 1. Code Placement
The production-grade Python script has been written directly to the project at:
*   [market_research.py](file:///E:/AI%20Startup/backend/app/agents/nodes/market_research.py)

---

## 2. Agent Workflow Mechanics

```mermaid
graph TD
    Start[State Input] --> RunNode[market_research_node]
    
    subgraph Execution Loop
        RunNode --> CheckKeys{API Keys Available?}
        CheckKeys -->|No| MockRun[Load Mock Dict Fallbacks]
        CheckKeys -->|Yes| LLMRun[Compile ChatPromptTemplate]
        
        LLMRun --> Bind[Bind structured_output: MarketResearchOutput]
        Bind --> Invoke[Invoke GPT-4o]
        
        Invoke -->|Network/429 Exception| Tenacity{Tenacity Retry < 3?}
        Tenacity -->|Yes| RetryWait[Exponential Backoff Wait]
        RetryWait --> Invoke
        Tenacity -->|No| Crash[Throw ParseException]
    end

    MockRun --> UpdateState[Save data to state['market_data']]
    Crash --> Fallback[Load zeroed safety indicators & logs error to state['errors']]
    Invoke -->|Success JSON| UpdateState
    Fallback --> UpdateState
    
    UpdateState --> End[Return State Dictionary]
```

---

## 3. Key Design Features

### A. Pydantic Structured Output
Instead of querying the LLM for plain text and relying on regex parser functions, this agent leverages `ChatOpenAI.with_structured_output(MarketResearchOutput)`. 
This guarantees the returned payload strictly complies with the Pydantic type model:
```python
class MarketResearchOutput(BaseModel):
    market_description: str
    market_size_billions: float
    tam_billions: float
    sam_billions: float
    som_billions: float
    cagr_percentage: float
    headwinds: List[str]
    tailwinds: List[str]
```
If GPT-4o fails to format the fields, LangChain raises a validation error, triggering the safety mechanisms.

### B. Tenacity Retry Mechanics
To mitigate cloud API connection drops or OpenAI 429 rate limit errors, queries are wrapped in retry filters:
*   **Multiplier:** `1` (initial wait)
*   **Wait Limits:** Min `2` seconds, Max `10` seconds (exponential backoff)
*   **Attempts:** `3` total attempts before crashing

### C. Graceful Fallback Strategy
If all 3 retries fail, the node doesn't crash the workflow. Instead:
1.  Logs details using python `logging` utility.
2.  Adds the traceback exception message to `state["errors"]["market_research"]`.
3.  Injects a zeroed-out validation dictionary payload into the state to avoid broken schema dependency crashes for down-stream nodes (e.g., Competitor, Risk, or Revenue nodes).

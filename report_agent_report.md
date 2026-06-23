# AI Startup Validator: Report Compiler Agent Specification

This document details the code capabilities, ReportLab styling, page flows, and output mapping of the **Report Compiler Agent**.

---

## 1. Code Placement
The production-grade Python script has been written directly to the project at:
*   [report_generation.py](file:///E:/AI%20Startup/backend/app/agents/nodes/report_generation.py)

---

## 2. Agent Workflow & PDF Compiler Mechanics

```mermaid
graph TD
    Start[State Input] --> RunNode[report_generation_node]
    
    subgraph Synthesis Loop
        RunNode --> LoadAll[Load outputs from all prior nodes]
        LoadAll --> CheckKeys{API Keys Available?}
        CheckKeys -->|No| MockRun[Load mock executive synthesis model]
        CheckKeys -->|Yes| LLMRun[Compile ChatPromptTemplate]
        
        LLMRun --> Bind[Bind structured_output: ReportSynthesisOutput]
        Bind --> Invoke[Invoke GPT-4o]
        
        Invoke -->|Network/429 Exception| Tenacity{Tenacity Retry < 3?}
        Tenacity -->|Yes| RetryWait[Exponential Backoff Wait]
        RetryWait --> Invoke
        Tenacity -->|No| Crash[Throw ParseException]
    end

    MockRun --> PDFCompile[Build ReportLab SimpleDocTemplate Flow]
    Invoke -->|Success JSON| PDFCompile
    Crash --> Fallback[Load failure indicators & logs error to state['errors']]
    
    Fallback --> PDFCompile
    PDFCompile --> WriteDisk[Save file to backend/static/reports/ID.pdf]
    WriteDisk --> UpdateState[Save PDF serve path & JSON details to state['report_data']]
    UpdateState --> End[Return State Dictionary]
```

---

## 3. Key Design Features

### A. Synthesis and Scoring Data Structure (`ReportSynthesisOutput`)
Prompts GPT-4o to act as a Chief Startup Officer to consolidate findings and output:
*   `executive_summary`
*   `overall_score` (0-100)
*   `market_opportunity_score` (0-100)
*   `investment_readiness_score` (0-100)
*   `revenue_potential_score` (0-100)
*   `key_recommendations` (Exactly 5 foundational action items)

### B. Premium ReportLab PDF Generator (`build_report_pdf`)
Generates a polished multi-page document matching modern styling parameters:
*   **Colors:** Deep Indigo (`#1A365D`) headers and borders; Teal (`#0D9488`) accent metrics; Soft Gray (`#F8FAFC`) backdrops.
*   **Structure:**
    *   *Page 1:* Title, metadata block (idea, target market, budget, customer segment), Executive Summary, and colored horizontal grid displaying the four key Scores.
    *   *Page 2:* Section 3 (Market TAM metrics data table) and Section 4 (Competitor analysis and customer personas).
    *   *Page 3:* Section 5 (3-year revenue forecast data table and break-even milestones), Section 6 (Critical risk audits with probabilities and impacts), and Section 7 (The 5 founder recommendations).
*   **Output Path:** Writes the file to the local directory `backend/static/reports/{project_id}.pdf` and returns the URL `/static/reports/{project_id}.pdf`.

### C. Tenacity and Integration
*   **Error Catching:** Catches compilation errors, writes them to `state["errors"]["report_generation"]`, and logs messages.
*   **Sandbox Safety:** If API credentials are not set, falls back to a template mock structure and generates the PDF file on disk, guaranteeing the server pipeline compiles.

import logging
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings
from app.agents.state import AgentState
from app.agents.llm import get_llm

logger = logging.getLogger("uvicorn.error")

# --- Pydantic Schema for Risk Detail ---
class RiskDetail(BaseModel):
    risk_category: str = Field(
        description="The risk category: Technical | Market | Financial | Legal | Operational."
    )
    risk_description: str = Field(
        description="Specific explanation of the risk threat and how it manifests."
    )
    probability: str = Field(
        description="Probability score: low | medium | high | critical"
    )
    impact: str = Field(
        description="Business impact severity score: low | medium | high | critical"
    )
    mitigation_strategy: str = Field(
        description="Actionable business/technical blueprint to mitigate or offset this risk."
    )

# --- Pydantic Schema for Agent JSON Output ---
class RiskAssessmentOutput(BaseModel):
    risks: List[RiskDetail] = Field(
        description="List of top 3 to 5 critical business risks."
    )

# --- Tenacity Retry Configuration ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True
)
def invoke_risk_llm(llm: Any, prompt_inputs: Dict[str, Any]) -> RiskAssessmentOutput:
    """Wrapper to query LLM with tenacity automatic retry parameters."""
    system_prompt = (
        "You are an expert Chief Risk Officer and Corporate Governance Risk Auditor Agent.\n"
        "Your role is to perform rigorous risk audits for startup concepts.\n"
        "Analyze the startup idea, budget, target market, and preceding findings from the Market Research, "
        "Competitor, Customer Persona, and Revenue Prediction Agents.\n"
        "Identify the top 3-5 critical risks across: Technical, Market, Financial, and Legal categories.\n"
        "Rate each risk's probability and impact (low/medium/high/critical) and formulate a clear, actionable mitigation blueprint."
    )
    
    human_prompt = (
        "Audit the business risks for the following startup:\n"
        "- Title: {idea_title}\n"
        "- Description: {idea_description}\n"
        "- Available Budget: ${budget}\n\n"
        "Incorporate the findings from previous research steps:\n"
        "1. Market Sizing Data:\n{market_data}\n"
        "2. Competitor Landscaping:\n{competitor_data}\n"
        "3. Customer Persona Demographics:\n{customer_data}\n"
        "4. Financial Revenue Projections:\n{revenue_data}\n\n"
        "Generate the structured risk audit."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # Bind structured output schema
    structured_llm = llm.with_structured_output(RiskAssessmentOutput)
    chain = prompt | structured_llm
    
    return chain.invoke(prompt_inputs)

# --- LangGraph Node Function ---
async def risk_assessment_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph Agent Node:
    Takes state inputs, requests risk evaluations from LLM, and maps them
    to the state['risk_data'] list.
    """
    node_name = "risk_assessment"
    logger.info(f"Executing Agent Node: {node_name}")
    
    llm = get_llm(temperature=0.1)
    if not llm:
        logger.warning("No LLM configured. Executing risk node with mock values.")
        # Fallback list of mock risks for dev/sandbox validation testing
        mock_risks = [
            {
                "risk_category": "Market",
                "risk_description": "Legacy competitor platforms releasing automated code refactoring engines natively.",
                "probability": "medium",
                "impact": "high",
                "mitigation_strategy": "Accelerate IDE integrations (SonarLint plug-ins) and secure enterprise feedback loops early."
            },
            {
                "risk_category": "Technical",
                "risk_description": "High LLM API execution token pricing limits margins on free code validation tiers.",
                "probability": "high",
                "impact": "medium",
                "mitigation_strategy": "Cache syntax checks using static regex and deploy lightweight local models (e.g. Llama-3) for routine tasks."
            },
            {
                "risk_category": "Legal",
                "risk_description": "Data residency laws (GDPR/CCPA) prohibiting third-party LLM transmission of proprietary codebases.",
                "probability": "medium",
                "impact": "critical",
                "mitigation_strategy": "Establish zero-retention API contracts with OpenAI or package the platform as a containerized VPC-deployable tool."
            }
        ]
        return {"risk_data": mock_risks}

    try:
        # Request structured response
        result: RiskAssessmentOutput = invoke_risk_llm(
            llm=llm,
            prompt_inputs={
                "idea_title": state["idea_title"],
                "idea_description": state["idea_description"],
                "budget": state["budget"],
                "market_data": json.dumps(state.get("market_data", {})),
                "competitor_data": json.dumps(state.get("competitor_data", [])),
                "customer_data": json.dumps(state.get("customer_data", [])),
                "revenue_data": json.dumps(state.get("revenue_data", []))
            }
        )
        
        # Serialize list of Pydantic risk details
        risks_list = [risk.model_dump() for risk in result.risks]
        return {"risk_data": risks_list}
        
    except Exception as e:
        logger.error(f"Error executing risk_assessment_node: {str(e)}")
        # Log error in state
        updated_errors = state.get("errors", {})
        updated_errors[node_name] = f"LLM Invocation Failed: {str(e)}"
        
        # Fallback list to prevent DB schema mapper crashes
        fallback_data = [
            {
                "risk_category": "General",
                "risk_description": "General system processing failure.",
                "probability": "medium",
                "impact": "medium",
                "mitigation_strategy": "Verify API connections and trace node errors."
            }
        ]
        
        return {
            "risk_data": fallback_data,
            "errors": updated_errors
        }

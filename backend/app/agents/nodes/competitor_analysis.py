import logging
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings
from app.agents.state import AgentState
from app.agents.llm import get_llm

logger = logging.getLogger("uvicorn.error")

# --- Pydantic Schema for Competitor Detail ---
class CompetitorDetail(BaseModel):
    competitor_name: str = Field(
        description="Name of the competitor company or product."
    )
    market_share: Optional[float] = Field(
        default=None,
        description="Estimated market share percentage (value between 0 and 100), if estimable."
    )
    pricing_model: str = Field(
        description="Competitor pricing model (e.g., Freemium starting at $15/user/month, flat-rate enterprise)."
    )
    key_features: List[str] = Field(
        description="Primary features and technical capabilities offered by this competitor."
    )
    market_positioning: str = Field(
        description="How the competitor positions their value proposition (e.g. premium enterprise safety, cheap self-serve tool)."
    )
    strengths: List[str] = Field(
        description="Strengths of the competitor (SWOT - Strengths)."
    )
    weaknesses: List[str] = Field(
        description="Weaknesses of the competitor (SWOT - Weaknesses)."
    )
    opportunities: List[str] = Field(
        description="Opportunities that this competitor is leaving open or that we can exploit (SWOT - Opportunities)."
    )
    threats: List[str] = Field(
        description="Vulnerabilities or direct competitive threats this competitor poses to our success (SWOT - Threats)."
    )
    threat_level: str = Field(
        description="The overall competitive threat level this player represents: low | medium | high | critical"
    )

# --- Pydantic Schema for Agent JSON Output ---
class CompetitorAnalysisOutput(BaseModel):
    competitors: List[CompetitorDetail] = Field(
        description="List of identified direct and indirect competitors."
    )
    saturation_summary: str = Field(
        description="An executive summary of the competitive landscape and market saturation level."
    )

# --- Tenacity Retry Configuration ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True
)
def invoke_competitor_llm(llm: Any, prompt_inputs: Dict[str, Any]) -> CompetitorAnalysisOutput:
    """Wrapper to query LLM with tenacity automatic retry parameters."""
    system_prompt = (
        "You are an expert, highly critical Competitor Intelligence Analyst Agent.\n"
        "Your role is to map the competitive landscape for startup concepts.\n"
        "Analyze the startup idea, target market, customer segment, and the preceding "
        "market research report. Identify direct and indirect competitors, dissect their "
        "pricing models, catalog their product capabilities, clarify their positioning, "
        "and produce a strict SWOT profile for each player.\n"
        "Be analytical, precise, and honest about potential threats."
    )
    
    human_prompt = (
        "Evaluate the competitive landscape for the following startup:\n"
        "- Title: {idea_title}\n"
        "- Description: {idea_description}\n"
        "- Target Market: {target_market}\n"
        "- Customer Segment: {customer_segment}\n\n"
        "Incorporate the following Market Sizing findings into your competitive positioning analysis:\n"
        "{market_data}\n\n"
        "Generate a structured competitive intelligence analysis."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    structured_llm = llm.with_structured_output(CompetitorAnalysisOutput)
    chain = prompt | structured_llm
    
    return chain.invoke(prompt_inputs)

# --- LangGraph Node Function ---
async def competitor_analysis_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph Agent Node:
    Takes state parameters and preceding market research, calls LLM,
    and returns list of competitor details inside state['competitor_data'].
    """
    node_name = "competitor_analysis"
    logger.info(f"Executing Agent Node: {node_name}")
    
    llm = get_llm(temperature=0.15)
    if not llm:
        logger.warning("No LLM configured. Executing competitor node with mock values.")
        # Fallback realistic mock values for sandbox/dev testing
        mock_competitors = [
            {
                "competitor_name": "SonarQube & SonarCloud",
                "market_share": 35.5,
                "pricing_model": "Freemium starting at $10/month based on lines of code. Enterprise plans range from $2,000 to $20,000/year.",
                "key_features": [
                    "Static Code Analysis (SAST)",
                    "IDE integration (SonarLint)",
                    "Quality Gate configurations",
                    "Support for 30+ languages"
                ],
                "market_positioning": "Standard legacy utility focusing on static quality criteria and compliance enforcement in big organizations.",
                "strengths": ["Huge market share", "Strong IDE integration", "Wide language compatibility"],
                "weaknesses": ["Slow analysis runtime", "Hard to configure rules", "High cost for enterprise code bases"],
                "opportunities": ["Improve developer experience", "Automate code fixes using LLMs rather than just warning"],
                "threats": ["Deep integration with existing CI/CD pipelines makes migration difficult"],
                "threat_level": "high"
            },
            {
                "competitor_name": "Snyk Code",
                "market_share": 12.0,
                "pricing_model": "Freemium tier, Team tier at $57/contributor/month, Custom corporate pricing.",
                "key_features": [
                    "Vulnerability scanning",
                    "License compliance checks",
                    "Automatic PR fixes",
                    "DevSecOps integrations"
                ],
                "market_positioning": "Security-first static analyzer geared toward fast deployment pipelines and open-source compliance.",
                "strengths": ["Excellent security database", "Developer-friendly interface", "Automated dependency updates"],
                "weaknesses": ["Less focus on code readability/styling", "Can produce high noise/false-positives"],
                "opportunities": ["Offer styling/refactoring insights in addition to security scans"],
                "threats": ["Expanding fast into developer workflows and code reviews"],
                "threat_level": "medium"
            }
        ]
        return {"competitor_data": mock_competitors}

    try:
        # Request structured response
        result: CompetitorAnalysisOutput = invoke_competitor_llm(
            llm=llm,
            prompt_inputs={
                "idea_title": state["idea_title"],
                "idea_description": state["idea_description"],
                "target_market": state["target_market"],
                "customer_segment": state["customer_segment"],
                "market_data": json.dumps(state.get("market_data", {}))
            }
        )
        
        # Serialize list of Pydantic competitor details
        competitors_list = [comp.model_dump() for comp in result.competitors]
        return {"competitor_data": competitors_list}
        
    except Exception as e:
        logger.error(f"Error executing competitor_analysis_node: {str(e)}")
        # Log error in state
        updated_errors = state.get("errors", {})
        updated_errors[node_name] = f"LLM Invocation Failed: {str(e)}"
        
        # Safe fallback
        fallback_data = [
            {
                "competitor_name": "Data unavailable",
                "market_share": None,
                "pricing_model": "Unavailable",
                "key_features": [],
                "market_positioning": "Unavailable",
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": [],
                "threat_level": "medium"
            }
        ]
        
        return {
            "competitor_data": fallback_data,
            "errors": updated_errors
        }

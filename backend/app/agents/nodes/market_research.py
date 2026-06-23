import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings
from app.agents.state import AgentState
from app.agents.llm import get_llm

logger = logging.getLogger("uvicorn.error")

# --- Pydantic Schema for Structured Output ---
class MarketResearchOutput(BaseModel):
    market_description: str = Field(
        description="Comprehensive summary of the current market landscape, size, key trends, and structure."
    )
    market_size_billions: float = Field(
        description="Total global/regional industry market size in billions of USD."
    )
    tam_billions: float = Field(
        description="Total Addressable Market (TAM) in billions of USD, representing the total market demand for your product/service."
    )
    sam_billions: float = Field(
        description="Serviceable Addressable Market (SAM) in billions of USD, the portion of the TAM that is targetable by your business model."
    )
    som_billions: float = Field(
        description="Serviceable Obtainable Market (SOM) in billions of USD, the share of SAM you can realistically capture within 1-3 years."
    )
    cagr_percentage: float = Field(
        description="Estimated Compound Annual Growth Rate (CAGR) percentage for this industry over the next 5 years."
    )
    headwinds: List[str] = Field(
        description="Major challenges, barriers to entry, risks, or negative growth factors affecting the market."
    )
    tailwinds: List[str] = Field(
        description="Key growth drivers, technical shifts, regulatory catalysts, or consumer demand increases."
    )

# --- Tenacity Retry Configuration ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True
)
def invoke_llm_with_retry(llm: Any, prompt_inputs: Dict[str, Any]) -> MarketResearchOutput:
    """Wrapper to query LLM with tenacity automatic retry parameters."""
    system_prompt = (
        "You are an expert, data-driven Venture Capital Market Analyst and Research Agent.\n"
        "Your goal is to perform rigorous market sizing and growth estimation for startup ideas.\n"
        "You must analyze the startup idea title, description, and targeted market, and calculate "
        "accurate estimates for TAM, SAM, SOM, CAGR, and market trends.\n"
        "Be conservative, realistic, and ensure calculations make mathematical sense (TAM >= SAM >= SOM)."
    )
    
    human_prompt = (
        "Perform market research on the following startup concept:\n"
        "- Title: {idea_title}\n"
        "- Description: {idea_description}\n"
        "- Target Market Segment: {target_market}\n"
        "- Intended Customer Segment: {customer_segment}\n\n"
        "Provide a detailed, professional estimation using the structured format."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # Force LLM to conform to the defined Pydantic JSON structure
    structured_llm = llm.with_structured_output(MarketResearchOutput)
    chain = prompt | structured_llm
    
    return chain.invoke(prompt_inputs)

# --- LangGraph Node Function ---
async def market_research_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph Agent Node:
    Takes project info from the State, invokes LLM with structured formatting,
    and populates `market_data` in the AgentState dictionary.
    """
    node_name = "market_research"
    logger.info(f"Executing Agent Node: {node_name}")
    
    llm = get_llm(temperature=0.1)
    if not llm:
        logger.warning("No LLM configured. Executing node with static mock values.")
        # Fallback to realistic mock values for sandbox/dev testing
        mock_data = {
            "market_description": "Mocked validation output: Artificial Intelligence automation market inside corporate security and operations segments.",
            "market_size_billions": 48.5,
            "tam_billions": 12.2,
            "sam_billions": 2.4,
            "som_billions": 0.45,
            "cagr_percentage": 18.5,
            "headwinds": [
                "Strict data protection regulations (GDPR/CCPA)",
                "High API computing expenses",
                "Vendor lock-in resistance"
            ],
            "tailwinds": [
                "Widespread corporate machine learning adoption",
                "Demand for developer review automation tools",
                "Increasing venture funding inside cloud architecture nodes"
            ]
        }
        return {"market_data": mock_data}

    try:
        # Request structured response
        research_result: MarketResearchOutput = invoke_llm_with_retry(
            llm=llm,
            prompt_inputs={
                "idea_title": state["idea_title"],
                "idea_description": state["idea_description"],
                "target_market": state["target_market"],
                "customer_segment": state["customer_segment"]
            }
        )
        
        # Convert Pydantic object to native dictionary
        market_data_dict = research_result.model_dump()
        return {"market_data": market_data_dict}
        
    except Exception as e:
        logger.error(f"Error executing market_research_node: {str(e)}")
        # Append node error details to State for workflow resilience
        updated_errors = state.get("errors", {})
        updated_errors[node_name] = f"LLM Invocation Failed: {str(e)}"
        
        # Provide degraded fallback to keep workflow alive
        fallback_data = {
            "market_description": "Data unavailable due to upstream processing issues.",
            "market_size_billions": 0.0,
            "tam_billions": 0.0,
            "sam_billions": 0.0,
            "som_billions": 0.0,
            "cagr_percentage": 0.0,
            "headwinds": ["Error parsing market metrics"],
            "tailwinds": ["Fallback mode activated"]
        }
        
        return {
            "market_data": fallback_data,
            "errors": updated_errors
        }

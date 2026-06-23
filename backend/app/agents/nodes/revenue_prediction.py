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

# --- Pydantic Schema for Yearly Forecast Detail ---
class YearlyForecastDetail(BaseModel):
    year: int = Field(
        description="The target year of projection (typically 1, 2, or 3)."
    )
    mrr: float = Field(
        description="Projected Monthly Recurring Revenue (MRR) at the end of the year in USD."
    )
    arr: float = Field(
        description="Projected Annual Recurring Revenue (ARR) at the end of the year in USD."
    )
    projected_revenue: float = Field(
        description="Total projected revenue generated during this specific year in USD."
    )
    projected_growth_rate: float = Field(
        description="Percentage revenue growth rate compared to the prior year (0.00 for Year 1)."
    )
    assumptions: List[str] = Field(
        description="List of core metrics backing this forecast (e.g., pricing model tier, conversion rate, customer count, CAC limits)."
    )

# --- Pydantic Schema for Agent JSON Output ---
class RevenuePredictionOutput(BaseModel):
    yearly_forecasts: List[YearlyForecastDetail] = Field(
        description="A list of exactly 3 years of financial projections."
    )
    months_to_breakeven: int = Field(
        description="Estimated number of months from launch to reach a break-even cash-flow state."
    )
    breakeven_explanation: str = Field(
        description="VC-level explanation of the cost metrics and unit economics required to achieve break-even."
    )

# --- Tenacity Retry Configuration ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True
)
def invoke_revenue_llm(llm: Any, prompt_inputs: Dict[str, Any]) -> RevenuePredictionOutput:
    """Wrapper to query LLM with tenacity automatic retry parameters."""
    system_prompt = (
        "You are an expert, highly quantitative SaaS Financial Architect and Revenue Prediction Agent.\n"
        "Your task is to generate realistic, data-driven 3-year revenue projections for startup ideas.\n"
        "Analyze the concept description, target segment, budget, and the preceding findings on market size "
        "and competitor pricing models.\n"
        "Incorporate conversion rate models, customer acquisition assumptions, and the budget constraints to "
        "model: 3-Year Revenue Forecast, MRR, ARR, and a clear Break-even Timeline prediction.\n"
        "Be financially logical: MRR * 12 should approximate ARR; Year 2/3 growth rates must align with assumptions."
    )
    
    human_prompt = (
        "Model the financial forecasts for the following startup:\n"
        "- Title: {idea_title}\n"
        "- Description: {idea_description}\n"
        "- Available Budget: ${budget}\n"
        "- Targeted Customers: {customer_segment}\n\n"
        "Incorporate the findings from previous research steps:\n"
        "1. Market TAM & Sizing:\n{market_data}\n"
        "2. Competitor Pricing Models:\n{competitor_data}\n"
        "3. Target Customer Persona Insights:\n{customer_data}\n\n"
        "Generate a structured 3-year financial forecast."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # Bind structured output schema
    structured_llm = llm.with_structured_output(RevenuePredictionOutput)
    chain = prompt | structured_llm
    
    return chain.invoke(prompt_inputs)

# --- LangGraph Node Function ---
async def revenue_prediction_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph Agent Node:
    Takes state inputs, requests financial forecasts from LLM, and maps them
    to the state['revenue_data'] list, while preserving breakeven metadata.
    """
    node_name = "revenue_prediction"
    logger.info(f"Executing Agent Node: {node_name}")
    
    llm = get_llm(temperature=0.1)
    if not llm:
        logger.warning("No LLM configured. Executing revenue node with mock values.")
        # Fallback list of mock projections for dev/sandbox validation testing
        mock_forecasts = [
            {
                "year": 1,
                "mrr": 10000.0,
                "arr": 120000.0,
                "projected_revenue": 120000.0,
                "projected_growth_rate": 0.0,
                "assumptions": ["Tier 1 pricing at $49/mo", "Capture 200 active customer seats", "1.5% conversion rate"]
            },
            {
                "year": 2,
                "mrr": 30000.0,
                "arr": 360000.0,
                "projected_revenue": 350000.0,
                "projected_growth_rate": 191.67,
                "assumptions": ["Launch enterprise tier at $299/mo", "Total base expands to 650 seats"]
            },
            {
                "year": 3,
                "mrr": 80000.0,
                "arr": 960000.0,
                "projected_revenue": 950000.0,
                "projected_growth_rate": 171.43,
                "assumptions": ["Self-serve channel optimization", "Partner integration channels open"]
            }
        ]
        return {
            "revenue_data": mock_forecasts,
            "revenue_metadata": {
                "months_to_breakeven": 8,
                "breakeven_explanation": "Break-even achieved in Month 8 as MRC expansion covers fixed host infrastructure and base salary costs."
            }
        }

    try:
        # Request structured response
        result: RevenuePredictionOutput = invoke_revenue_llm(
            llm=llm,
            prompt_inputs={
                "idea_title": state["idea_title"],
                "idea_description": state["idea_description"],
                "budget": state["budget"],
                "customer_segment": state["customer_segment"],
                "market_data": json.dumps(state.get("market_data", {})),
                "competitor_data": json.dumps(state.get("competitor_data", [])),
                "customer_data": json.dumps(state.get("customer_data", []))
            }
        )
        
        # Format projections into db-compatible structure
        forecasts_list = []
        for f in result.yearly_forecasts:
            # Append MRR/ARR details into assumptions array so it gets stored in the DB without schema modifications
            extended_assumptions = [
                f"Projected Year-End MRR: ${f.mrr:,.2f}",
                f"Projected Year-End ARR: ${f.arr:,.2f}"
            ] + f.assumptions
            
            forecasts_list.append({
                "year": f.year,
                "projected_revenue": f.projected_revenue,
                "projected_growth_rate": f.projected_growth_rate,
                "assumptions": extended_assumptions
            })
            
        return {
            "revenue_data": forecasts_list,
            "revenue_metadata": {
                "months_to_breakeven": result.months_to_breakeven,
                "breakeven_explanation": result.breakeven_explanation
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing revenue_prediction_node: {str(e)}")
        # Log error in state
        updated_errors = state.get("errors", {})
        updated_errors[node_name] = f"LLM Invocation Failed: {str(e)}"
        
        # Fallback list to prevent DB schema mapper crashes
        fallback_data = [
            {
                "year": 1,
                "projected_revenue": 0.0,
                "projected_growth_rate": 0.0,
                "assumptions": ["Revenue predictions failed."]
            }
        ]
        
        return {
            "revenue_data": fallback_data,
            "errors": updated_errors
        }

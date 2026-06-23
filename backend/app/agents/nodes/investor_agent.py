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

# --- Pydantic Schema for Investor Partner Review ---
class InvestorPartnerReview(BaseModel):
    investor_persona_name: str = Field(
        description="The Venture Capital Partner persona (e.g., 'B2B SaaS Seed Partner', 'DeepTech Early-Stage GP')."
    )
    investment_verdict: str = Field(
        description="The investment recommendation recommendation verdict: invest | watch | pass"
    )
    market_opportunity_analysis: str = Field(
        description="Venture assessment of market size, trends, timing, and customer segment viability."
    )
    business_model_analysis: str = Field(
        description="Review of business scalability, CAC/LTV dynamics, and pricing models."
    )
    competition_analysis: str = Field(
        description="Critique of competitor positioning, saturation level, and entry barriers."
    )
    defensibility_analysis: str = Field(
        description="Evaluation of product moat, network effects, IP strategy, or tech defensibility."
    )
    risk_analysis: str = Field(
        description="Evaluation of regulatory, technical, operational, and founder execution risks."
    )
    strengths: List[str] = Field(
        description="Top investment strengths (why this startup represents an attractive opportunity)."
    )
    weaknesses: List[str] = Field(
        description="Primary concerns, missing parameters, or pass rationale."
    )
    score_out_of_10: int = Field(
        description="Overall investment score rating from 1 (lowest) to 10 (highest).",
        ge=1,
        le=10
    )

# --- Pydantic Schema for Agent JSON Output ---
class InvestorAgentOutput(BaseModel):
    reviews: List[InvestorPartnerReview] = Field(
        description="Evaluations from the VC investment committee partners (contains 1 or 2 partners)."
    )

# --- Tenacity Retry Configuration ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True
)
def invoke_investor_llm(llm: Any, prompt_inputs: Dict[str, Any]) -> InvestorAgentOutput:
    """Wrapper to query LLM with tenacity automatic retry parameters."""
    system_prompt = (
        "You are an expert Venture Capital Investment Partner auditing startup investment opportunities.\n"
        "Your role is to simulate an investment committee review. Analyze the startup idea, budget, "
        "target segment, and preceding findings from the Market Research, Competitor, and Revenue Agents.\n"
        "Assess: Market Opportunity, Business Model, Competition, Defensibility, and Founder/Execution Risk.\n"
        "Deliver a clear recommendation (invest/watch/pass), key strengths/weaknesses, and a score out of 10.\n"
        "Be extremely objective, skeptical, and look for structural vulnerabilities."
    )
    
    human_prompt = (
        "Conduct an investment evaluation for the following startup:\n"
        "- Title: {idea_title}\n"
        "- Description: {idea_description}\n"
        "- Budget: ${budget}\n"
        "- Customer Segment: {customer_segment}\n\n"
        "Analyze this in the context of the preceding agent findings:\n"
        "1. Market Sizing Data:\n{market_data}\n"
        "2. Competitor Landscaping:\n{competitor_data}\n"
        "3. Financial Revenue Projections:\n{revenue_data}\n\n"
        "Generate the structured investment review."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # Bind structured output schema
    structured_llm = llm.with_structured_output(InvestorAgentOutput)
    chain = prompt | structured_llm
    
    return chain.invoke(prompt_inputs)

# --- LangGraph Node Function ---
async def investor_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph Agent Node:
    Takes state inputs, requests VC review evaluations from LLM, and maps them
    to the state['investor_data'] list, adapting score/details to DB schemas.
    """
    node_name = "investor_agent"
    logger.info(f"Executing Agent Node: {node_name}")
    
    llm = get_llm(temperature=0.1)
    if not llm:
        logger.warning("No LLM configured. Executing investor node with mock values.")
        # Fallback VC partner mock profile for dev/sandbox validation testing
        mock_review = [
            {
                "investor_persona_name": "SaaS Venture Capital GP",
                "investment_verdict": "watch",
                "feedback_details": (
                    "### Market Opportunity\n"
                    "Attractive segment within SaaS code security, but TAM might be limited to corporate pipelines.\n\n"
                    "### Business Model\n"
                    "Healthy recurring seat pricing margins, but requires customer validation validation.\n\n"
                    "### Key Strengths\n"
                    "- Strong developer tooling tailwinds\n"
                    "- Automated PR fixing reduces seat churn\n\n"
                    "### Key Weaknesses\n"
                    "- Heavy initial marketing CAC barrier\n"
                    "- Regulatory audit complexities"
                ),
                "investment_score": 70  # mapped from 7 out of 10
            }
        ]
        return {"investor_data": mock_review}

    try:
        # Request structured response
        result: InvestorAgentOutput = invoke_investor_llm(
            llm=llm,
            prompt_inputs={
                "idea_title": state["idea_title"],
                "idea_description": state["idea_description"],
                "budget": state["budget"],
                "customer_segment": state["customer_segment"],
                "market_data": json.dumps(state.get("market_data", {})),
                "competitor_data": json.dumps(state.get("competitor_data", [])),
                "revenue_data": json.dumps(state.get("revenue_data", []))
            }
        )
        
        # Transform results to DB-compatible structure
        formatted_reviews = []
        for review in result.reviews:
            # Build clean markdown text for feedback details
            feedback_md = (
                f"### Market Opportunity\n{review.market_opportunity_analysis}\n\n"
                f"### Business Model\n{review.business_model_analysis}\n\n"
                f"### Competition\n{review.competition_analysis}\n\n"
                f"### Defensibility & Moat\n{review.defensibility_analysis}\n\n"
                f"### Execution & Founder Risks\n{review.risk_analysis}\n\n"
                f"### Key Strengths\n* " + "\n* ".join(review.strengths) + "\n\n"
                f"### Key Weaknesses\n* " + "\n* ".join(review.weaknesses)
            )
            
            # Map score out of 10 to database 0-100 scale
            db_score = int(min(max(review.score_out_of_10, 1), 10) * 10)
            
            formatted_reviews.append({
                "investor_persona_name": review.investor_persona_name,
                "investment_verdict": review.investment_verdict.lower(),
                "feedback_details": feedback_md,
                "investment_score": db_score
            })
            
        return {"investor_data": formatted_reviews}
        
    except Exception as e:
        logger.error(f"Error executing investor_agent_node: {str(e)}")
        # Log error in state
        updated_errors = state.get("errors", {})
        updated_errors[node_name] = f"LLM Invocation Failed: {str(e)}"
        
        # Fallback profile
        fallback_data = [
            {
                "investor_persona_name": "Investment Committee",
                "investment_verdict": "pass",
                "feedback_details": "VC review failed during pipeline execution.",
                "investment_score": 0
            }
        ]
        
        return {
            "investor_data": fallback_data,
            "errors": updated_errors
        }

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

# --- Pydantic Schema for Persona ---
class CustomerPersonaDetail(BaseModel):
    name: str = Field(
        description="Descriptive name of the persona (e.g. Early-stage CTO, Solo Freelancer)."
    )
    age: int = Field(
        description="Realistic age estimation for this demographic profile."
    )
    occupation: str = Field(
        description="Primary profession, role, or title."
    )
    buying_power: str = Field(
        description="Capacity to spend: low | medium | high"
    )
    pain_points: List[str] = Field(
        description="Exactly 3 specific, critical frustrations or challenges this persona faces related to our startup concept."
    )
    willingness_to_pay: str = Field(
        description="Pricing sensitivity and payment behavior (e.g. high sensitivity, prefers subscriptions under $50/mo)."
    )

# --- Pydantic Schema for Agent JSON Output ---
class CustomerPersonaOutput(BaseModel):
    personas: List[CustomerPersonaDetail] = Field(
        description="List of top 2-3 target user profiles."
    )

# --- Tenacity Retry Configuration ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True
)
def invoke_customer_llm(llm: Any, prompt_inputs: Dict[str, Any]) -> CustomerPersonaOutput:
    """Wrapper to query LLM with tenacity automatic retry parameters."""
    system_prompt = (
        "You are an expert Ideal Customer Profile (ICP) Persona Auditor and Product Strategist Agent.\n"
        "Your task is to design detailed, demographically and behaviorally logical personas "
        "for startup concepts based on target market sizing outputs.\n"
        "Generate 2 to 3 distinct target profiles, including their age, occupation, buying power, "
        "frustrations, and exact willingness to pay specifications.\n"
        "Ensure pain points directly align with the core problem statement of the startup concept."
    )
    
    human_prompt = (
        "Audit customer personas for the following startup:\n"
        "- Title: {idea_title}\n"
        "- Description: {idea_description}\n"
        "- Customer Segment Bounds: {customer_segment}\n\n"
        "Incorporate the findings from the preceding Market Sizing step:\n"
        "{market_data}\n\n"
        "Generate the structured customer persona catalog."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # Bind structured output schema
    structured_llm = llm.with_structured_output(CustomerPersonaOutput)
    chain = prompt | structured_llm
    
    return chain.invoke(prompt_inputs)

# --- LangGraph Node Function ---
async def customer_persona_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph Agent Node:
    Takes state inputs, requests customer persona generation from LLM,
    and returns a structured catalog of personas inside state['customer_data'].
    """
    node_name = "customer_persona"
    logger.info(f"Executing Agent Node: {node_name}")
    
    llm = get_llm(temperature=0.2)
    if not llm:
        logger.warning("No LLM configured. Executing customer node with mock values.")
        # Fallback list of mock personas for dev/sandbox validation testing
        mock_personas = [
            {
                "persona_name": "Developer Devin",
                "demographics": {"age": 28, "occupation": "Software Engineer", "buying_power": "Medium"},
                "pain_points": [
                    "Wasteful time spent on code styling arguments during pull request reviews",
                    "Debugging syntax formatting quirks across different projects",
                    "Missing hidden bugs due to tedious manual PR reviews"
                ],
                "buying_behavior": "Willingness to pay: Medium. Prefers personal subscriptions up to $15/month."
            },
            {
                "persona_name": "CTO Clara",
                "demographics": {"age": 42, "occupation": "VP of Engineering / CTO", "buying_power": "High"},
                "pain_points": [
                    "High developer overhead hours spent reviewing basic code layout guidelines",
                    "Inconsistent code formatting styles across disjointed team branches",
                    "Security policy drift between junior commits and production builds"
                ],
                "buying_behavior": "Willingness to pay: High. Budget-holder for team tools up to $49/developer/month."
            }
        ]
        return {"customer_data": mock_personas}

    try:
        # Request structured response
        result: CustomerPersonaOutput = invoke_customer_llm(
            llm=llm,
            prompt_inputs={
                "idea_title": state["idea_title"],
                "idea_description": state["idea_description"],
                "customer_segment": state["customer_segment"],
                "market_data": json.dumps(state.get("market_data", {}))
            }
        )
        
        # Format personas into database-compatible structure
        formatted_personas = []
        for persona in result.personas:
            formatted_personas.append({
                "persona_name": persona.name,
                "demographics": {
                    "age": persona.age,
                    "occupation": persona.occupation,
                    "buying_power": persona.buying_power
                },
                "pain_points": persona.pain_points,
                "buying_behavior": f"Willingness to pay: {persona.willingness_to_pay}"
            })
            
        return {"customer_data": formatted_personas}
        
    except Exception as e:
        logger.error(f"Error executing customer_persona_node: {str(e)}")
        # Log error in state
        updated_errors = state.get("errors", {})
        updated_errors[node_name] = f"LLM Invocation Failed: {str(e)}"
        
        # Fallback data structure to satisfy DB mapper
        fallback_data = [
            {
                "persona_name": "Fallback User Profile",
                "demographics": {"age": 30, "occupation": "Professional", "buying_power": "Medium"},
                "pain_points": ["System parsing failure"],
                "buying_behavior": "Willingness to pay: Unknown"
            }
        ]
        
        return {
            "customer_data": fallback_data,
            "errors": updated_errors
        }

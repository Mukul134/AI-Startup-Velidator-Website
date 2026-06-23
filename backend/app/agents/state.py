from typing import Any, Dict, List, TypedDict, Optional, Annotated

def merge_errors(left: Dict[str, str], right: Dict[str, str]) -> Dict[str, str]:
    if left is None:
        left = {}
    if right is None:
        right = {}
    return {**left, **right}

class AgentState(TypedDict):
    # Base Inputs
    idea_title: str
    idea_description: str
    target_market: str
    budget: float
    customer_segment: str
    
    # Internal context data
    project_id: str
    
    # Node outputs
    market_data: Optional[Dict[str, Any]]
    competitor_data: Optional[List[Dict[str, Any]]]
    customer_data: Optional[List[Dict[str, Any]]]
    revenue_data: Optional[List[Dict[str, Any]]]
    risk_data: Optional[List[Dict[str, Any]]]
    investor_data: Optional[List[Dict[str, Any]]]
    report_data: Optional[Dict[str, Any]]
    
    # System meta
    errors: Annotated[Dict[str, str], merge_errors]
    current_node: str

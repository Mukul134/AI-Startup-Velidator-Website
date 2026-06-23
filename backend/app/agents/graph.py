from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes.market_research import market_research_node
from app.agents.nodes.competitor_analysis import competitor_analysis_node
from app.agents.nodes.customer_persona import customer_persona_node
from app.agents.nodes.investor_agent import investor_agent_node
from app.agents.nodes.revenue_prediction import revenue_prediction_node
from app.agents.nodes.risk_assessment import risk_assessment_node
from app.agents.nodes.report_generation import report_generation_node

def create_workflow():
    # Initialize state graph
    workflow = StateGraph(AgentState)
    
    # Register Nodes
    workflow.add_node("market", market_research_node)
    workflow.add_node("competitor", competitor_analysis_node)
    workflow.add_node("customer", customer_persona_node)
    workflow.add_node("revenue", revenue_prediction_node)
    workflow.add_node("risk", risk_assessment_node)
    workflow.add_node("investor", investor_agent_node)
    workflow.add_node("report", report_generation_node)
    
    # Set Entry Point
    workflow.set_entry_point("market")
    
    # Configure Parallel Branching from Market Research
    workflow.add_edge("market", "competitor")
    workflow.add_edge("market", "customer")
    workflow.add_edge("market", "revenue")
    
    # Set up joins.
    # Risk Assessment requires competitor and customer data.
    workflow.add_edge("competitor", "risk")
    workflow.add_edge("customer", "risk")
    
    # Investor reviews require market, competitor, and revenue data.
    # We pipe revenue and competitor into investor.
    workflow.add_edge("revenue", "investor")
    
    # Connect risks and investment reviews to final reporting
    workflow.add_edge("risk", "report")
    workflow.add_edge("investor", "report")
    
    # Compile graph
    workflow.add_edge("report", END)
    
    return workflow.compile()

app_workflow = create_workflow()

import os
import logging
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings
from app.agents.state import AgentState
from app.agents.llm import get_llm

# ReportLab Imports for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger("uvicorn.error")

# --- Pydantic Schema for Synthesized Report Output ---
class ReportSynthesisOutput(BaseModel):
    executive_summary: str = Field(
        description="A high-level executive summary of the startup idea's overall viability, market fit, and execution feasibility."
    )
    overall_score: int = Field(
        description="Combined overall viability score from 0 (failed) to 100 (exceptional validation status).",
        ge=0,
        le=100
    )
    market_opportunity_score: int = Field(
        description="Market opportunity score from 0 to 100 based on TAM sizing and growthCAGRs.",
        ge=0,
        le=100
    )
    investment_readiness_score: int = Field(
        description="Investment readiness score from 0 to 100 based on investor feedback and metrics.",
        ge=0,
        le=100
    )
    revenue_potential_score: int = Field(
        description="Revenue potential score from 0 to 100 based on 3-year projected models.",
        ge=0,
        le=100
    )
    key_recommendations: List[str] = Field(
        description="Exactly 5 critical, actionable recommendations for the founders to execute next."
    )

# --- Tenacity Retry Configuration ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True
)
def invoke_report_llm(llm: Any, prompt_inputs: Dict[str, Any]) -> ReportSynthesisOutput:
    """Wrapper to query LLM with tenacity automatic retry parameters."""
    system_prompt = (
        "You are an expert Chief Startup Officer and Report Synthesis Agent.\n"
        "Your task is to compile and synthesize findings from all previous agent nodes into a single, cohesive, "
        "investor-grade startup validation report.\n"
        "Analyze the market TAM, competitive SWOTs, target personas, revenue projections, and VC review verdicts.\n"
        "Generate a professional Executive Summary, calculate logical scoring indexes (Overall, Market, Investment, "
        "Revenue Potential), and formulate 5 highly specific action items.\n"
        "Ensure the summary is detailed, constructive, and free of vague generalizations."
    )
    
    human_prompt = (
        "Synthesize a final report for the following startup:\n"
        "- Title: {idea_title}\n"
        "- Description: {idea_description}\n"
        "- Initial Budget: ${budget}\n"
        "- Target Segment: {customer_segment}\n\n"
        "Synthesize findings from these preceding steps:\n"
        "1. Market Sizing Data:\n{market_data}\n"
        "2. Competitor Sizing & Positionings:\n{competitor_data}\n"
        "3. Target Customer Personas:\n{customer_data}\n"
        "4. Projected Financial Revenue Projections:\n{revenue_data}\n"
        "5. VC Investor Reviews:\n{investor_data}\n"
        "6. Risk Audits:\n{risk_data}\n\n"
        "Generate the structured validation synthesis."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    # Bind structured output schema
    structured_llm = llm.with_structured_output(ReportSynthesisOutput)
    chain = prompt | structured_llm
    
    return chain.invoke(prompt_inputs)

# --- PDF Builder Utility ---
def build_report_pdf(project_id: str, state: AgentState, report_data: Dict[str, Any]) -> str:
    """Generates a beautifully styled, premium-grade validation PDF report."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "reports")
    os.makedirs(static_dir, exist_ok=True)
    pdf_filename = f"{project_id}.pdf"
    pdf_path = os.path.join(static_dir, pdf_filename)
    
    # Setup document template
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Premium Color Palette
    PRIMARY_COLOR = colors.HexColor("#1A365D")  # Deep Indigo
    SECONDARY_COLOR = colors.HexColor("#0D9488") # Vibrant Teal
    DARK_TEXT = colors.HexColor("#1E293B")       # Dark Charcoal
    LIGHT_BG = colors.HexColor("#F8FAFC")        # Off-white / light slate
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=DARK_TEXT,
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=DARK_TEXT,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    meta_header_style = ParagraphStyle(
        'MetaHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white
    )
    
    meta_val_style = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.white
    )

    story = []
    
    # --- Page 1: Header / Document Title ---
    story.append(Paragraph("AI Startup Validator - Validation Report", title_style))
    story.append(Spacer(1, 10))
    
    # Idea Brief Metadata Block
    meta_data = [
        [Paragraph("Project ID", meta_header_style), Paragraph(str(project_id), meta_val_style)],
        [Paragraph("Startup Idea", meta_header_style), Paragraph(state["idea_title"], meta_val_style)],
        [Paragraph("Target Market", meta_header_style), Paragraph(state["target_market"], meta_val_style)],
        [Paragraph("Initial Capital", meta_header_style), Paragraph(f"${state['budget']:,.2f} USD", meta_val_style)],
        [Paragraph("Customer Focus", meta_header_style), Paragraph(state["customer_segment"], meta_val_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[120, 400])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY_COLOR),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, SECONDARY_COLOR),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    # --- Executive Summary & Scoring Section ---
    story.append(Paragraph("1. Executive Summary & Viability Scores", section_title_style))
    story.append(Paragraph(report_data["executive_summary"], body_style))
    story.append(Spacer(1, 10))
    
    # Viability Scores Grid Table
    score_header_style = ParagraphStyle('ScoreHead', fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=1)
    score_val_style = ParagraphStyle('ScoreVal', fontName='Helvetica-Bold', fontSize=16, leading=18, alignment=1, textColor=SECONDARY_COLOR)
    
    scores_data = [
        [
            Paragraph("Overall Viability", score_header_style),
            Paragraph("Market Fit", score_header_style),
            Paragraph("Investment Grade", score_header_style),
            Paragraph("Revenue Potential", score_header_style)
        ],
        [
            Paragraph(f"{report_data['overall_score']}/100", score_val_style),
            Paragraph(f"{report_data['market_opportunity_score']}/100", score_val_style),
            Paragraph(f"{report_data['investment_readiness_score']}/100", score_val_style),
            Paragraph(f"{report_data['revenue_potential_score']}/100", score_val_style)
        ]
    ]
    
    scores_table = Table(scores_data, colWidths=[130, 130, 130, 130])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, PRIMARY_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 20))
    
    # --- Market Research Sizing Data ---
    m_data = state.get("market_data") or {}
    story.append(Paragraph("2. Market Opportunity Sizing", section_title_style))
    story.append(Paragraph(m_data.get("market_description", "No description provided."), body_style))
    
    market_metrics = [
        [Paragraph("Target Market size", body_style), Paragraph(f"${m_data.get('market_size_billions', 0.0)} Billion", body_style)],
        [Paragraph("TAM (Total Addressable Market)", body_style), Paragraph(f"${m_data.get('tam_billions', 0.0)} Billion", body_style)],
        [Paragraph("SAM (Serviceable Addressable Market)", body_style), Paragraph(f"${m_data.get('sam_billions', 0.0)} Billion", body_style)],
        [Paragraph("SOM (Serviceable Obtainable Market)", body_style), Paragraph(f"${m_data.get('som_billions', 0.0)} Billion", body_style)],
        [Paragraph("Projected CAGR", body_style), Paragraph(f"{m_data.get('cagr_percentage', 0.0)}%", body_style)]
    ]
    market_table = Table(market_metrics, colWidths=[200, 320])
    market_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))
    story.append(market_table)
    story.append(PageBreak())
    
    # --- Page 2: Competitor & Customer Persona Profiles ---
    story.append(Paragraph("3. Competitive Saturation Profiles", section_title_style))
    comps = state.get("competitor_data") or []
    for comp in comps:
        comp_summary = (
            f"<b>{comp.get('competitor_name')}</b> (Threat: {comp.get('threat_level', 'medium').upper()})<br/>"
            f"Pricing: {comp.get('pricing_model', 'N/A')}<br/>"
            f"Strengths: {', '.join(comp.get('strengths', []))}<br/>"
            f"Weaknesses: {', '.join(comp.get('weaknesses', []))}"
        )
        story.append(Paragraph(comp_summary, body_style))
        story.append(Spacer(1, 4))
        
    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Customer Persona Mapping", section_title_style))
    personas = state.get("customer_data") or []
    for pers in personas:
        demo = pers.get("demographics", {})
        pers_summary = (
            f"<b>{pers.get('persona_name')}</b> ({demo.get('occupation', 'Professional')}, Age {demo.get('age', 30)})<br/>"
            f"Pain Points: {', '.join(pers.get('pain_points', []))}<br/>"
            f"{pers.get('buying_behavior')}"
        )
        story.append(Paragraph(pers_summary, body_style))
        story.append(Spacer(1, 4))
        
    story.append(PageBreak())
    
    # --- Page 3: Projections & Risk Audits ---
    story.append(Paragraph("5. Financial Revenue Projections", section_title_style))
    revs = state.get("revenue_data") or []
    rev_rows = [[Paragraph("Year", score_header_style), Paragraph("Projected Annual Revenue", score_header_style), Paragraph("Growth Rate", score_header_style)]]
    for r in revs:
        rev_rows.append([
            Paragraph(f"Year {r.get('year')}", body_style),
            Paragraph(f"${r.get('projected_revenue', 0.0):,.2f} USD", body_style),
            Paragraph(f"{r.get('projected_growth_rate', 0.0)}%", body_style)
        ])
    rev_table = Table(rev_rows, colWidths=[100, 250, 170])
    rev_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))
    story.append(rev_table)
    
    # Add Break-even metadata if available
    rev_meta = state.get("revenue_metadata") or {}
    if "months_to_breakeven" in rev_meta:
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Time to Break-even:</b> {rev_meta.get('months_to_breakeven')} Months", body_style))
        story.append(Paragraph(rev_meta.get("breakeven_explanation", ""), body_style))
        
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("6. Critical Investment Risk Audits", section_title_style))
    risks = state.get("risk_data") or []
    for risk in risks:
        risk_summary = (
            f"• <b>[{risk.get('risk_category')}]</b> {risk.get('risk_description')}<br/>"
            f"Probability: {risk.get('probability', 'medium').upper()} | Impact: {risk.get('impact', 'medium').upper()}<br/>"
            f"Mitigation: {risk.get('mitigation_strategy')}"
        )
        story.append(Paragraph(risk_summary, body_style))
        story.append(Spacer(1, 4))
        
    story.append(Spacer(1, 10))
    story.append(Paragraph("7. Actionable Founder Recommendations", section_title_style))
    for idx, rec in enumerate(report_data["key_recommendations"]):
        story.append(Paragraph(f"<b>{idx+1}.</b> {rec}", bullet_style))
        
    # Compile pages
    doc.build(story)
    
    # Return serve URL relative to API host
    return f"/static/reports/{pdf_filename}"

# --- LangGraph Node Function ---
async def report_generation_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph Agent Node:
    Takes all state inputs, queries LLM for final report details and score indexes,
    triggers ReportLab PDF compile, and saves outcomes in state['report_data'].
    """
    node_name = "report_generation"
    logger.info(f"Executing Agent Node: {node_name}")
    project_id = state["project_id"]
    
    llm = get_llm(temperature=0.2)
    if not llm:
        logger.warning("No LLM configured. Executing report node with mock values.")
        mock_report = {
            "executive_summary": "Mock Validation Report: The concept is viable with high market sizing, but exhibits moderate competitor saturation threats.",
            "overall_score": 75,
            "market_opportunity_score": 85,
            "investment_readiness_score": 70,
            "revenue_potential_score": 72,
            "key_recommendations": [
                "Establish initial pilot validation checks with VP of Engineering candidates.",
                "Build unique AI code styling moats rather than copying SonarQube features.",
                "Optimize starting budget toward product dev instead of immediate corporate sales.",
                "Verify security and pipeline integration architectures.",
                "Focus seed pitches on developer productivity CAGR tailwinds."
            ]
        }
        
        # Build local mock PDF report
        try:
            pdf_url = build_report_pdf(project_id, state, mock_report)
            mock_report["pdf_report_url"] = pdf_url
        except Exception as e:
            logger.error(f"Failed build mock PDF report: {str(e)}")
            
        return {"report_data": mock_report}

    try:
        # Request structured response
        result: ReportSynthesisOutput = invoke_report_llm(
            llm=llm,
            prompt_inputs={
                "idea_title": state["idea_title"],
                "idea_description": state["idea_description"],
                "budget": state["budget"],
                "customer_segment": state["customer_segment"],
                "market_data": json.dumps(state.get("market_data", {})),
                "competitor_data": json.dumps(state.get("competitor_data", [])),
                "customer_data": json.dumps(state.get("customer_data", [])),
                "revenue_data": json.dumps(state.get("revenue_data", [])),
                "investor_data": json.dumps(state.get("investor_data", [])),
                "risk_data": json.dumps(state.get("risk_data", []))
            }
        )
        
        # Convert model output to dictionary
        report_data_dict = {
            "executive_summary": result.executive_summary,
            "overall_score": result.overall_score,
            "market_opportunity_score": result.market_opportunity_score,
            "investment_readiness_score": result.investment_readiness_score,
            "revenue_potential_score": result.revenue_potential_score,
            "key_recommendations": result.key_recommendations
        }
        
        # Build PDF and obtain URL path
        try:
            pdf_url = build_report_pdf(project_id, state, report_data_dict)
            report_data_dict["pdf_report_url"] = pdf_url
        except Exception as pdf_err:
            logger.error(f"Failed to generate PDF document: {str(pdf_err)}")
            report_data_dict["pdf_report_url"] = None
            
        return {"report_data": report_data_dict}
        
    except Exception as e:
        logger.error(f"Error executing report_generation_node: {str(e)}")
        # Log error in state
        updated_errors = state.get("errors", {})
        updated_errors[node_name] = f"LLM Invocation Failed: {str(e)}"
        
        fallback_data = {
            "executive_summary": "Failed to compile validation report findings.",
            "overall_score": 0,
            "market_opportunity_score": 0,
            "investment_readiness_score": 0,
            "revenue_potential_score": 0,
            "key_recommendations": ["System processing timeout"],
            "pdf_report_url": None
        }
        
        return {
            "report_data": fallback_data,
            "errors": updated_errors
        }

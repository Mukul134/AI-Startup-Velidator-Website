from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.entities import ProjectStatus, ThreatLevel, InvestmentVerdict, RiskLevel

# --- USER SCHEMAS ---
class UserRead(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- PROJECT SCHEMAS ---
class ProjectCreate(BaseModel):
    idea_title: str = Field(..., max_length=255, examples=["Automated Code Reviewer"])
    idea_description: str = Field(..., examples=["An AI tool that performs pull request checks."])
    target_market: str = Field(..., max_length=255, examples=["Global SaaS firms"])
    budget: float = Field(..., gt=0, examples=[50000.00])
    customer_segment: str = Field(..., max_length=255, examples=["VP of Engineering"])

class ProjectRead(BaseModel):
    id: UUID
    user_id: UUID
    idea_title: str
    idea_description: str
    target_market: str
    budget: float
    customer_segment: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- SUB-REPORT DETAILS SCHEMAS ---
class CompetitorSchema(BaseModel):
    competitor_name: str
    market_share: Optional[float] = None
    strengths: List[str]
    weaknesses: List[str]
    threat_level: ThreatLevel

    class Config:
        from_attributes = True

class CustomerPersonaSchema(BaseModel):
    persona_name: str
    demographics: Dict[str, Any]
    pain_points: List[str]
    buying_behavior: Optional[str] = None

    class Config:
        from_attributes = True

class InvestorReviewSchema(BaseModel):
    investor_persona_name: str
    investment_verdict: InvestmentVerdict
    feedback_details: str
    investment_score: Optional[int] = None

    class Config:
        from_attributes = True

class RiskAssessmentSchema(BaseModel):
    risk_category: str
    risk_description: str
    probability: RiskLevel
    impact: RiskLevel
    mitigation_strategy: Optional[str] = None

    class Config:
        from_attributes = True

class RevenuePredictionSchema(BaseModel):
    year: int
    projected_revenue: float
    projected_growth_rate: Optional[float] = None
    assumptions: List[str]

    class Config:
        from_attributes = True

# --- REPORT SCHEMAS ---
class ReportRead(BaseModel):
    id: UUID
    project_id: UUID
    executive_summary: Optional[str] = None
    overall_score: Optional[int] = None
    pdf_report_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FullReportDetails(BaseModel):
    project: ProjectRead
    report: Optional[ReportRead] = None
    competitors: List[CompetitorSchema] = []
    personas: List[CustomerPersonaSchema] = []
    investor_reviews: List[InvestorReviewSchema] = []
    risk_assessments: List[RiskAssessmentSchema] = []
    revenue_predictions: List[RevenuePredictionSchema] = []

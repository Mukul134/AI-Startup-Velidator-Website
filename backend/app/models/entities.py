from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from enum import Enum
from sqlalchemy import Enum as SAEnum, ARRAY, String

# --- ENUMS ---
class ProjectStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class InvestmentVerdict(str, Enum):
    INVEST = "invest"
    WATCH = "watch"
    PASS = "pass"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PaymentStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"

# --- DB ENTITIES ---

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: UUID = Field(primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    full_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    projects: List["StartupProject"] = Relationship(back_populates="user", cascade_delete=True)


class StartupProject(SQLModel, table=True):
    __tablename__ = "startup_projects"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    idea_title: str = Field(nullable=False)
    idea_description: str = Field(nullable=False)
    target_market: str = Field(nullable=False)
    budget: float = Field(default=0.0, nullable=False)
    customer_segment: str = Field(nullable=False)
    status: ProjectStatus = Field(
        sa_column=Column(
            SAEnum(ProjectStatus, name="project_status", values_callable=lambda x: [e.value for e in x]),
            nullable=False,
            default=ProjectStatus.PENDING
        )
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional[User] = Relationship(back_populates="projects")
    report: Optional["Report"] = Relationship(
        back_populates="project", 
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )
    competitors: List["CompetitorAnalysis"] = Relationship(back_populates="project", cascade_delete=True)
    personas: List["CustomerPersona"] = Relationship(back_populates="project", cascade_delete=True)
    investor_reviews: List["InvestorReview"] = Relationship(back_populates="project", cascade_delete=True)
    risk_assessments: List["RiskAssessment"] = Relationship(back_populates="project", cascade_delete=True)
    revenue_predictions: List["RevenuePrediction"] = Relationship(back_populates="project", cascade_delete=True)


class Report(SQLModel, table=True):
    __tablename__ = "reports"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="startup_projects.id", unique=True, nullable=False)
    executive_summary: Optional[str] = Field(default=None)
    overall_score: Optional[int] = Field(default=None)
    pdf_report_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[StartupProject] = Relationship(back_populates="report")


class CompetitorAnalysis(SQLModel, table=True):
    __tablename__ = "competitor_analysis"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="startup_projects.id", nullable=False)
    competitor_name: str = Field(nullable=False)
    market_share: Optional[float] = Field(default=None)
    strengths: List[str] = Field(default=[], sa_type=ARRAY(String))
    weaknesses: List[str] = Field(default=[], sa_type=ARRAY(String))
    threat_level: ThreatLevel = Field(
        sa_column=Column(
            SAEnum(ThreatLevel, name="threat_level_type", values_callable=lambda x: [e.value for e in x]),
            nullable=False,
            default=ThreatLevel.MEDIUM
        )
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[StartupProject] = Relationship(back_populates="competitors")


class CustomerPersona(SQLModel, table=True):
    __tablename__ = "customer_personas"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="startup_projects.id", nullable=False)
    persona_name: str = Field(nullable=False)
    demographics: Dict[str, Any] = Field(default={}, sa_type=JSON)
    pain_points: List[str] = Field(default=[], sa_type=ARRAY(String))
    buying_behavior: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[StartupProject] = Relationship(back_populates="personas")


class InvestorReview(SQLModel, table=True):
    __tablename__ = "investor_reviews"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="startup_projects.id", nullable=False)
    investor_persona_name: str = Field(nullable=False)
    investment_verdict: InvestmentVerdict = Field(
        sa_column=Column(
            SAEnum(InvestmentVerdict, name="investment_verdict_type", values_callable=lambda x: [e.value for e in x]),
            nullable=False,
            default=InvestmentVerdict.PASS
        )
    )
    feedback_details: str = Field(nullable=False)
    investment_score: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[StartupProject] = Relationship(back_populates="investor_reviews")


class RiskAssessment(SQLModel, table=True):
    __tablename__ = "risk_assessments"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="startup_projects.id", nullable=False)
    risk_category: str = Field(nullable=False)
    risk_description: str = Field(nullable=False)
    probability: RiskLevel = Field(
        sa_column=Column(
            SAEnum(RiskLevel, name="risk_level_type", values_callable=lambda x: [e.value for e in x]),
            nullable=False
        )
    )
    impact: RiskLevel = Field(
        sa_column=Column(
            SAEnum(RiskLevel, name="risk_level_type", values_callable=lambda x: [e.value for e in x]),
            nullable=False
        )
    )
    mitigation_strategy: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[StartupProject] = Relationship(back_populates="risk_assessments")


class RevenuePrediction(SQLModel, table=True):
    __tablename__ = "revenue_predictions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="startup_projects.id", nullable=False)
    year: int = Field(nullable=False)
    projected_revenue: float = Field(nullable=False)
    projected_growth_rate: Optional[float] = Field(default=0.0)
    assumptions: List[str] = Field(default=[], sa_type=ARRAY(String))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[StartupProject] = Relationship(back_populates="revenue_predictions")


class PaymentRecord(SQLModel, table=True):
    __tablename__ = "payment_records"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    plan_code: str = Field(nullable=False)
    amount_inr: int = Field(nullable=False)
    currency: str = Field(default="INR", nullable=False)
    status: PaymentStatus = Field(
        sa_column=Column(
            SAEnum(PaymentStatus, name="payment_status_type", values_callable=lambda x: [e.value for e in x]),
            nullable=False,
            default=PaymentStatus.CREATED,
        )
    )
    razorpay_order_id: str = Field(nullable=False, index=True)
    razorpay_payment_id: Optional[str] = Field(default=None, index=True)
    razorpay_signature: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

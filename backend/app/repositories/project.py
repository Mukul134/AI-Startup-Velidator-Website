from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import UUID
from typing import List, Optional
from app.models.entities import (
    StartupProject,
    Report,
    CompetitorAnalysis,
    CustomerPersona,
    InvestorReview,
    RiskAssessment,
    RevenuePrediction,
    ProjectStatus
)
from app.schemas.project import ProjectCreate, FullReportDetails

class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, user_id: UUID, project_in: ProjectCreate) -> StartupProject:
        """Create a new startup project entry in database."""
        db_project = StartupProject(
            user_id=user_id,
            idea_title=project_in.idea_title,
            idea_description=project_in.idea_description,
            target_market=project_in.target_market,
            budget=project_in.budget,
            customer_segment=project_in.customer_segment,
            status=ProjectStatus.PENDING
        )
        self.db.add(db_project)
        await self.db.commit()
        await self.db.refresh(db_project)
        return db_project

    async def get_project_by_id(self, project_id: UUID) -> Optional[StartupProject]:
        """Fetch project metadata by ID."""
        statement = select(StartupProject).where(StartupProject.id == project_id)
        result = await self.db.execute(statement)
        return result.scalars().first()

    async def list_projects_by_user(self, user_id: UUID) -> List[StartupProject]:
        """List all project validation histories for a user."""
        statement = select(StartupProject).where(StartupProject.user_id == user_id).order_by(StartupProject.created_at.desc())
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def update_project_status(self, project_id: UUID, status: ProjectStatus) -> Optional[StartupProject]:
        """Update status of a project run."""
        project = await self.get_project_by_id(project_id)
        if project:
            project.status = status
            self.db.add(project)
            await self.db.commit()
            await self.db.refresh(project)
        return project

    async def get_full_report_details(self, project_id: UUID) -> Optional[FullReportDetails]:
        """Joins and queries all tables relating to a project's compiled validation report."""
        project = await self.get_project_by_id(project_id)
        if not project:
            return None

        # Fetch sub-records
        report_stmt = select(Report).where(Report.project_id == project_id)
        report_res = await self.db.execute(report_stmt)
        report = report_res.scalars().first()

        comp_stmt = select(CompetitorAnalysis).where(CompetitorAnalysis.project_id == project_id)
        comp_res = await self.db.execute(comp_stmt)
        competitors = list(comp_res.scalars().all())

        pers_stmt = select(CustomerPersona).where(CustomerPersona.project_id == project_id)
        pers_res = await self.db.execute(pers_stmt)
        personas = list(pers_res.scalars().all())

        inv_stmt = select(InvestorReview).where(InvestorReview.project_id == project_id)
        inv_res = await self.db.execute(inv_stmt)
        investor_reviews = list(inv_res.scalars().all())

        risk_stmt = select(RiskAssessment).where(RiskAssessment.project_id == project_id)
        risk_res = await self.db.execute(risk_stmt)
        risk_assessments = list(risk_res.scalars().all())

        rev_stmt = select(RevenuePrediction).where(RevenuePrediction.project_id == project_id).order_by(RevenuePrediction.year.asc())
        rev_res = await self.db.execute(rev_stmt)
        revenue_predictions = list(rev_res.scalars().all())

        return FullReportDetails(
            project=project,
            report=report,
            competitors=competitors,
            personas=personas,
            investor_reviews=investor_reviews,
            risk_assessments=risk_assessments,
            revenue_predictions=revenue_predictions
        )

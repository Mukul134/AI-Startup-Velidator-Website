import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.entities import (
    StartupProject,
    Report,
    CompetitorAnalysis,
    CustomerPersona,
    InvestorReview,
    RiskAssessment,
    RevenuePrediction,
    ProjectStatus,
    ThreatLevel,
    InvestmentVerdict,
    RiskLevel
)
from app.agents.graph import app_workflow
from app.repositories.project import ProjectRepository

logger = logging.getLogger("uvicorn.error")

class ProjectValidationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)

    async def execute_validation_workflow(self, project_id: UUID) -> None:
        """Runs the LangGraph multi-agent validator and writes output to db."""
        from app.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            repo = ProjectRepository(db)
            project = await repo.get_project_by_id(project_id)
            if not project:
                logger.error(f"Project {project_id} not found for validation execution.")
                return

            # Update status to processing
            await repo.update_project_status(project_id, ProjectStatus.PROCESSING)
            
            # Prepare LangGraph state inputs
            initial_state = {
                "idea_title": project.idea_title,
                "idea_description": project.idea_description,
                "target_market": project.target_market,
                "budget": project.budget,
                "customer_segment": project.customer_segment,
                "project_id": str(project_id),
                "errors": {},
                "current_node": ""
            }

            try:
                # Invoke LangGraph workflow
                result = await app_workflow.ainvoke(initial_state)
                
                # --- Check for severe execution failures ---
                if "report_data" not in result or not result["report_data"]:
                    raise ValueError("Report agent failed to compile aggregated findings.")

                # --- 1. Write Competitors ---
                competitors = result.get("competitor_data") or []
                for comp in competitors:
                    db_comp = CompetitorAnalysis(
                        project_id=project_id,
                        competitor_name=comp.get("competitor_name", "Unknown"),
                        market_share=comp.get("market_share"),
                        strengths=comp.get("strengths", []),
                        weaknesses=comp.get("weaknesses", []),
                        threat_level=ThreatLevel(comp.get("threat_level", "medium").lower())
                    )
                    db.add(db_comp)

                # --- 2. Write Customer Personas ---
                personas = result.get("customer_data") or []
                for pers in personas:
                    db_pers = CustomerPersona(
                        project_id=project_id,
                        persona_name=pers.get("persona_name", "User Persona"),
                        demographics=pers.get("demographics", {}),
                        pain_points=pers.get("pain_points", []),
                        buying_behavior=pers.get("buying_behavior")
                    )
                    db.add(db_pers)

                # --- 3. Write Investor Reviews ---
                reviews = result.get("investor_data") or []
                for rev in reviews:
                    db_rev = InvestorReview(
                        project_id=project_id,
                        investor_persona_name=rev.get("investor_persona_name", "Angel"),
                        investment_verdict=InvestmentVerdict(rev.get("investment_verdict", "pass").lower()),
                        feedback_details=rev.get("feedback_details", "No feedback provided."),
                        investment_score=rev.get("investment_score")
                    )
                    db.add(db_rev)

                # --- 4. Write Risks ---
                risks = result.get("risk_data") or []
                for risk in risks:
                    db_risk = RiskAssessment(
                        project_id=project_id,
                        risk_category=risk.get("risk_category", "General"),
                        risk_description=risk.get("risk_description", ""),
                        probability=RiskLevel(risk.get("probability", "medium").lower()),
                        impact=RiskLevel(risk.get("impact", "medium").lower()),
                        mitigation_strategy=risk.get("mitigation_strategy")
                    )
                    db.add(db_risk)

                # --- 5. Write Revenue Forecast ---
                forecasts = result.get("revenue_data") or []
                for forecast in forecasts:
                    db_forecast = RevenuePrediction(
                        project_id=project_id,
                        year=forecast.get("year", 1),
                        projected_revenue=forecast.get("projected_revenue", 0.0),
                        projected_growth_rate=forecast.get("projected_growth_rate", 0.0),
                        assumptions=forecast.get("assumptions", [])
                    )
                    db.add(db_forecast)

                # --- 6. Write Consolidated Report ---
                report_data = result["report_data"]
                db_report = Report(
                    project_id=project_id,
                    executive_summary=report_data.get("executive_summary", ""),
                    overall_score=report_data.get("overall_score", 50),
                    pdf_report_url=report_data.get("pdf_report_url")
                )
                db.add(db_report)

                # Commit everything and set project status to completed
                await db.commit()
                await repo.update_project_status(project_id, ProjectStatus.COMPLETED)
                logger.info(f"Successfully processed validation project {project_id}")

            except Exception as e:
                logger.error(f"Failed workflow validation for project {project_id}: {str(e)}")
                await db.rollback()
                await repo.update_project_status(project_id, ProjectStatus.FAILED)

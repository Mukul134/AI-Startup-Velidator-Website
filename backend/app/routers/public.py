from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from sqlmodel import select
from app.database import get_db_session
from app.models.entities import StartupProject, Report, User
from app.schemas.billing import PricingTierRead, PublicOverviewRead
from app.services.catalog import get_pricing_tiers

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/pricing", response_model=list[PricingTierRead])
async def get_pricing():
    return get_pricing_tiers()


@router.get("/overview", response_model=PublicOverviewRead)
async def get_overview(db: AsyncSession = Depends(get_db_session)):
    total_projects = (await db.execute(select(func.count()).select_from(StartupProject))).scalar_one()
    completed_reports = (await db.execute(select(func.count()).select_from(Report))).scalar_one()
    active_founders = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    average_score = (await db.execute(select(func.avg(Report.overall_score)).select_from(Report))).scalar()

    return PublicOverviewRead(
        total_projects=total_projects or 0,
        completed_reports=completed_reports or 0,
        active_founders=active_founders or 0,
        average_score=int(round(average_score or 0)),
    )

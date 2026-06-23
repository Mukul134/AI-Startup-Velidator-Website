from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.database import get_db_session
from app.models.entities import User, StartupProject
from app.schemas.project import ProjectCreate, ProjectRead, FullReportDetails
from app.services.auth import get_current_user
from app.services.project import ProjectValidationService
from app.repositories.project import ProjectRepository

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectRead, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    project_in: ProjectCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submits a new startup idea for validation. 
    Returns immediately with a 202 status and handles analysis inside a background task.
    """
    repo = ProjectRepository(db)
    # Save base project model in db with pending status
    project = await repo.create_project(user_id=current_user.id, project_in=project_in)
    
    # Schedule the workflow in background
    validation_service = ProjectValidationService(db)
    background_tasks.add_task(
        validation_service.execute_validation_workflow,
        project_id=project.id
    )
    
    return project


@router.get("/", response_model=List[ProjectRead])
async def list_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve history of validations submitted by the user."""
    repo = ProjectRepository(db)
    projects = await repo.list_projects_by_user(user_id=current_user.id)
    return projects


@router.get("/{id}", response_model=ProjectRead)
async def get_project(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve the tracking metadata for a specific validation run."""
    repo = ProjectRepository(db)
    project = await repo.get_project_by_id(project_id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project validation")
        
    return project


@router.get("/{id}/report", response_model=FullReportDetails)
async def view_report(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve the compiled multi-agent reports for a validation run."""
    repo = ProjectRepository(db)
    project = await repo.get_project_by_id(project_id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this report")
        
    # Check if report has run to completion
    report_details = await repo.get_full_report_details(project_id=id)
    if not report_details or not report_details.report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report validation status is '{project.status}' and cannot be retrieved yet."
        )
        
    return report_details

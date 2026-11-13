from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.dependencies import get_current_db
from app.schemas import CompanyCreate, CompanyUpdate, CompanyResponse
from app.models import Company, Project
from app.services.langgraph_workflow import blog_generation_workflow
from app.services.project_cleanup import delete_project_artifacts

router = APIRouter()


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_current_db),
):
    """Create a new company."""
    db_company = Company(**company.model_dump())
    db.add(db_company)
    await db.commit()
    await db.refresh(db_company)
    return db_company


@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_current_db),
):
    """List all companies."""
    result = await db.execute(select(Company).offset(skip).limit(limit))
    companies = result.scalars().all()
    return companies


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Get a company by ID."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    db: AsyncSession = Depends(get_current_db),
):
    """Update a company."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = company_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)
    return company


@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Delete a company and all of its projects (with generated artifacts)."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    projects = (
        await db.execute(select(Project).where(Project.company_id == company_id))
    ).scalars().all()
    for project in projects:
        await delete_project_artifacts(db, project.id)
        await db.delete(project)
        await blog_generation_workflow.reset_workflow(project.id)

    await db.delete(company)
    await db.commit()
    return {"message": "Company deleted successfully"}

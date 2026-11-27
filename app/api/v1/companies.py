from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.api.dependencies import get_current_db
from app.schemas import CompanyCreate, CompanyUpdate, CompanyResponse
from app.models import Company, Project, SqlWebsite
from app.services.langgraph_workflow import blog_generation_workflow
from app.services.project_cleanup import delete_project_artifacts
from app.site_connector.encryption import encrypt, decrypt
from app.site_connector.oauth import get_authorization_url, exchange_code_for_token
from app.site_connector.schemas import WordPressOAuthUrlResponse, WordPressOAuthCallbackRequest

router = APIRouter()


async def _set_sql_flags(db: AsyncSession, company: Company, response: CompanyResponse) -> None:
    """Populate SQL website flags on a company response."""
    count = (
        await db.execute(
            select(func.count(SqlWebsite.id)).where(SqlWebsite.company_id == company.id)
        )
    ).scalar_one()
    response.sql_websites_count = count
    response.sql_configured = count > 0


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_current_db),
):
    """Create a new company."""
    company_data = company.model_dump()
    
    # Encrypt sensitive WordPress credentials
    if company_data.get('wp_client_id'):
        company_data['wp_client_id'] = encrypt(company_data['wp_client_id'])
    if company_data.get('wp_client_secret'):
        company_data['wp_client_secret'] = encrypt(company_data['wp_client_secret'])
    
    db_company = Company(**company_data)
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
    
    # Set wp_configured flag based on whether all WordPress credentials exist
    # Note: wp_token is optional and obtained through OAuth flow separately
    response = CompanyResponse.model_validate(company)
    response.wp_configured = bool(company.wp_site and company.wp_client_id and company.wp_client_secret)
    await _set_sql_flags(db, company, response)
    return response


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
    
    # Encrypt sensitive WordPress credentials
    if 'wp_client_id' in update_data and update_data['wp_client_id']:
        update_data['wp_client_id'] = encrypt(update_data['wp_client_id'])
    if 'wp_client_secret' in update_data and update_data['wp_client_secret']:
        update_data['wp_client_secret'] = encrypt(update_data['wp_client_secret'])
    if 'wp_token' in update_data and update_data['wp_token']:
        update_data['wp_token'] = encrypt(update_data['wp_token'])
    
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)
    
    # Set wp_configured flag based on whether all WordPress credentials exist
    # Note: wp_token is optional and obtained through OAuth flow separately
    response = CompanyResponse.model_validate(company)
    response.wp_configured = bool(company.wp_site and company.wp_client_id and company.wp_client_secret)
    await _set_sql_flags(db, company, response)
    return response


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


# WordPress OAuth endpoints
@router.post("/{company_id}/wordpress/oauth/url", response_model=WordPressOAuthUrlResponse)
async def get_wordpress_oauth_url(
    company_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Get WordPress OAuth authorization URL for a company."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if not company.wp_client_id:
        raise HTTPException(status_code=400, detail="WordPress client ID not configured for this company")
    
    redirect_uri = company.wp_redirect_uri or "http://127.0.0.1:8765/callback"
    
    # Decrypt client_id
    try:
        client_id = decrypt(company.wp_client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to decrypt client ID")
    
    auth_url, state = get_authorization_url(client_id, redirect_uri)
    
    return WordPressOAuthUrlResponse(
        authorization_url=auth_url,
        state=state
    )


@router.post("/{company_id}/wordpress/oauth/callback")
async def exchange_wordpress_oauth_code(
    company_id: int,
    callback: WordPressOAuthCallbackRequest,
    db: AsyncSession = Depends(get_current_db),
):
    """Exchange WordPress OAuth authorization code for access token."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if not all([company.wp_client_id, company.wp_client_secret]):
        raise HTTPException(status_code=400, detail="WordPress credentials not configured for this company")
    
    try:
        client_id = decrypt(company.wp_client_id)
        client_secret = decrypt(company.wp_client_secret)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to decrypt credentials")
    
    redirect_uri = company.wp_redirect_uri or "http://127.0.0.1:8765/callback"
    
    try:
        token_data = exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=callback.code,
            redirect_uri=redirect_uri,
            site=company.wp_site,
        )
        
        # Encrypt and store the access token
        company.wp_token = encrypt(token_data["access_token"])
        await db.commit()
        await db.refresh(company)
        
        return {
            "message": "OAuth token successfully obtained and stored",
            "token_type": token_data.get("token_type"),
            "scope": token_data.get("scope"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth token exchange failed: {str(e)}")

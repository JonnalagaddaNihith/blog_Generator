import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_workflow_status(client: AsyncClient):
    """Test getting workflow status for a project."""
    # Create a company and project first
    company_response = await client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "description": "A test company"}
    )
    company_id = company_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects/",
        json={
            "company_id": company_id,
            "topic": "AI in Healthcare",
            "target_word_count": 1500
        }
    )
    project_id = project_response.json()["id"]

    response = await client.get(f"/api/v1/projects/{project_id}/workflow/status")
    assert response.status_code == 200
    data = response.json()
    assert "project_id" in data
    assert "current_stage" in data
    assert "persistence_status" in data


@pytest.mark.asyncio
async def test_workflow_status_invalid_project(client: AsyncClient):
    """Test getting workflow status for invalid project."""
    response = await client.get("/api/v1/projects/99999/workflow/status")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_retry_persistence_without_content(client: AsyncClient):
    """Test retry_persistence action when no blog content exists."""
    # Create a company and project first
    company_response = await client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "description": "A test company"}
    )
    company_id = company_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects/",
        json={
            "company_id": company_id,
            "topic": "AI in Healthcare",
            "target_word_count": 1500
        }
    )
    project_id = project_response.json()["id"]

    # Try to retry persistence without having started workflow
    response = await client.post(
        f"/api/v1/projects/{project_id}/workflow/approve",
        json={"action": "retry_persistence"}
    )
    assert response.status_code == 400
    assert "No blog content available" in response.json()["detail"]

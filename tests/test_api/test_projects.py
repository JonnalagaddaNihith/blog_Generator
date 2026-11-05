import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    """Test creating a project."""
    # Create a company first
    company_response = await client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "description": "A test company"}
    )
    company_id = company_response.json()["id"]

    response = await client.post(
        "/api/v1/projects/",
        json={
            "company_id": company_id,
            "topic": "AI in Healthcare",
            "target_word_count": 1500,
            "audience": "Healthcare professionals",
            "tone": "Professional"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "AI in Healthcare"
    assert data["target_word_count"] == 1500
    assert data["company_id"] == company_id


@pytest.mark.asyncio
async def test_create_project_invalid_company(client: AsyncClient):
    """Test creating a project with invalid company ID."""
    response = await client.post(
        "/api/v1/projects/",
        json={
            "company_id": 99999,
            "topic": "AI in Healthcare",
            "target_word_count": 1500
        }
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    """Test listing projects."""
    # Create a company and project first
    company_response = await client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "description": "A test company"}
    )
    company_id = company_response.json()["id"]

    await client.post(
        "/api/v1/projects/",
        json={
            "company_id": company_id,
            "topic": "AI in Healthcare",
            "target_word_count": 1500
        }
    )

    response = await client.get("/api/v1/projects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    """Test getting a project by ID."""
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

    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["topic"] == "AI in Healthcare"


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    """Test updating a project."""
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

    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"topic": "AI in Finance", "target_word_count": 2000}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "AI in Finance"
    assert data["target_word_count"] == 2000


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    """Test deleting a project."""
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

    response = await client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200

    # Verify it's deleted
    get_response = await client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 404

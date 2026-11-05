import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_company(client: AsyncClient):
    """Test creating a company."""
    response = await client.post(
        "/api/v1/companies/",
        json={
            "name": "Test Company",
            "description": "A test company",
            "website": "https://example.com"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Company"
    assert data["description"] == "A test company"
    assert data["website"] == "https://example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_companies(client: AsyncClient):
    """Test listing companies."""
    # Create a company first
    await client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "description": "A test company"}
    )

    response = await client.get("/api/v1/companies/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_company(client: AsyncClient):
    """Test getting a company by ID."""
    # Create a company first
    create_response = await client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "description": "A test company"}
    )
    company_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == company_id
    assert data["name"] == "Test Company"


@pytest.mark.asyncio
async def test_update_company(client: AsyncClient):
    """Test updating a company."""
    # Create a company first
    create_response = await client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "description": "A test company"}
    )
    company_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/companies/{company_id}",
        json={"name": "Updated Company", "description": "Updated description"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Company"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_company(client: AsyncClient):
    """Test deleting a company."""
    # Create a company first
    create_response = await client.post(
        "/api/v1/companies/",
        json={"name": "Test Company", "description": "A test company"}
    )
    company_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200

    # Verify it's deleted
    get_response = await client.get(f"/api/v1/companies/{company_id}")
    assert get_response.status_code == 404

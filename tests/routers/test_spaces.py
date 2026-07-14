import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_space(host_client: AsyncClient, sample_space_data):
    response = await host_client.post("/spaces", json=sample_space_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == sample_space_data["title"]
    assert data["price"] == sample_space_data["price"]
    assert "id" in data

@pytest.mark.asyncio
async def test_get_space(host_client: AsyncClient, sample_space_data):
    # Create
    create_response = await host_client.post("/spaces", json=sample_space_data)
    space_id = create_response.json()["id"]

    # Get
    response = await host_client.get(f"/spaces/{space_id}")
    assert response.status_code == 200
    assert response.json()["id"] == space_id

@pytest.mark.asyncio
async def test_update_space(host_client: AsyncClient, sample_space_data):
    # Create
    create_response = await host_client.post("/spaces", json=sample_space_data)
    space_id = create_response.json()["id"]

    # Update
    update_data = {"title": "Piscina Atualizada", "price": 150.0}
    response = await host_client.put(f"/spaces/{space_id}", json=update_data)
    assert response.status_code == 200
    
    # Verify update
    get_response = await host_client.get(f"/spaces/{space_id}")
    assert get_response.json()["title"] == "Piscina Atualizada"
    assert get_response.json()["price"] == 150.0

@pytest.mark.asyncio
async def test_delete_space(host_client: AsyncClient, sample_space_data):
    # Create
    create_response = await host_client.post("/spaces", json=sample_space_data)
    space_id = create_response.json()["id"]

    # Delete
    response = await host_client.delete(f"/spaces/{space_id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = await host_client.get(f"/spaces/{space_id}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_list_spaces(client: AsyncClient, host_client: AsyncClient, sample_space_data):
    # Create an approved space first (requires admin usually, but let's test the endpoint anyway)
    await host_client.post("/spaces", json=sample_space_data)
    
    response = await client.get("/spaces")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_autocomplete_spaces(client: AsyncClient):
    response = await client.get("/spaces/autocomplete?q=rio")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

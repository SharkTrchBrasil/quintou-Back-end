import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_booking(auth_client: AsyncClient, host_client: AsyncClient, sample_space_data, sample_booking_data):
    # Create space first
    space_resp = await host_client.post("/spaces", json=sample_space_data)
    space_id = space_resp.json()["id"]

    # Create booking
    sample_booking_data["space_id"] = space_id
    response = await auth_client.post("/bookings", json=sample_booking_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["space_id"] == space_id
    assert "id" in data
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_get_booking(auth_client: AsyncClient, host_client: AsyncClient, sample_space_data, sample_booking_data):
    # Create space and booking
    space_resp = await host_client.post("/spaces", json=sample_space_data)
    space_id = space_resp.json()["id"]
    sample_booking_data["space_id"] = space_id
    booking_resp = await auth_client.post("/bookings", json=sample_booking_data)
    booking_id = booking_resp.json()["id"]

    # Get
    response = await auth_client.get(f"/bookings/{booking_id}")
    assert response.status_code == 200
    assert response.json()["id"] == booking_id

@pytest.mark.asyncio
async def test_cancel_booking(auth_client: AsyncClient, host_client: AsyncClient, sample_space_data, sample_booking_data):
    # Create space and booking
    space_resp = await host_client.post("/spaces", json=sample_space_data)
    space_id = space_resp.json()["id"]
    sample_booking_data["space_id"] = space_id
    booking_resp = await auth_client.post("/bookings", json=sample_booking_data)
    booking_id = booking_resp.json()["id"]

    # Cancel
    response = await auth_client.put(f"/bookings/{booking_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

@pytest.mark.asyncio
async def test_list_bookings(auth_client: AsyncClient, host_client: AsyncClient, sample_space_data, sample_booking_data):
    space_resp = await host_client.post("/spaces", json=sample_space_data)
    space_id = space_resp.json()["id"]
    sample_booking_data["space_id"] = space_id
    await auth_client.post("/bookings", json=sample_booking_data)

    response = await auth_client.get("/bookings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_payment_intent(auth_client: AsyncClient, host_client: AsyncClient, sample_space_data, sample_booking_data):
    # 1. Create space
    space_resp = await host_client.post("/spaces", json=sample_space_data)
    space_id = space_resp.json()["id"]
    
    # 2. Create booking
    sample_booking_data["space_id"] = space_id
    booking_resp = await auth_client.post("/bookings", json=sample_booking_data)
    booking_id = booking_resp.json()["id"]

    # 3. Create payment intent
    response = await auth_client.post(
        "/payments/create-intent",
        json={"booking_id": booking_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert "client_secret" in data
    assert "payment_id" in data
    assert data["amount"] == 400.0
    assert data["currency"] == "brl"

@pytest.mark.asyncio
async def test_create_stripe_onboarding_not_host(auth_client: AsyncClient):
    response = await auth_client.post("/payments/onboarding")
    assert response.status_code == 403
    assert "Apenas anfitriões" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_stripe_onboarding_as_host(client: AsyncClient, test_user, db_session, sample_user_data):
    # Tornar user host
    test_user.is_host = True
    test_user.cpf = "12345678909"
    await db_session.commit()
    
    from app.services.auth_service import AuthService
    auth_service = AuthService(db_session)
    token = await auth_service.create_access_token(test_user.id)
    client.headers.update({"Authorization": f"Bearer {token.access_token}"})

    response = await client.post("/payments/onboarding")
    assert response.status_code == 200
    assert "url" in response.json()

@pytest.mark.asyncio
async def test_check_stripe_status(client: AsyncClient, test_user, db_session):
    # Make host and add stripe account id
    test_user.is_host = True
    test_user.stripe_account_id = "acct_mock123"
    await db_session.commit()
    
    from app.services.auth_service import AuthService
    auth_service = AuthService(db_session)
    token = await auth_service.create_access_token(test_user.id)
    client.headers.update({"Authorization": f"Bearer {token.access_token}"})

    response = await client.get("/payments/onboarding/status")
    assert response.status_code == 200
    assert response.json()["stripe_onboarding_complete"] == True

@pytest.mark.asyncio
async def test_stripe_webhook_invalid_sig(client: AsyncClient):
    response = await client.post("/payments/webhook", json={"type": "payment_intent.succeeded"})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_stripe_webhook_valid(client: AsyncClient, monkeypatch):
    import stripe
    # Bypass webhook construction logic
    def mock_construct(*args, **kwargs):
        return {"id": "evt_123", "type": "payment_intent.succeeded", "data": {"object": {"id": "pi_123"}}}
    
    monkeypatch.setattr(stripe.Webhook, "construct_event", mock_construct)
    
    response = await client.post("/payments/webhook", json={})
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

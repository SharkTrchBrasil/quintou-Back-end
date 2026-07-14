"""
Tests for authentication endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestRegistration:
    """Tests for user registration"""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, sample_user_data):
        """Test successful registration"""
        response = await client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, sample_user_data):
        """Test registration with duplicate email"""
        # First registration
        await client.post("/auth/register", json=sample_user_data)
        
        # Try to register again
        response = await client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "já cadastrado" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient, sample_user_data):
        """Test registration with weak password"""
        sample_user_data["password"] = "weak"
        response = await client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "senha" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_invalid_cpf(self, client: AsyncClient, sample_user_data):
        """Test registration with invalid CPF"""
        sample_user_data["cpf"] = "12345678900"  # Invalid checksum
        response = await client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "cpf" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient, sample_user_data):
        """Test registration with invalid email"""
        sample_user_data["email"] = "invalid-email"
        response = await client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for user login"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user_data):
        """Test successful login"""
        # Register first
        await client.post("/auth/register", json=sample_user_data)
        
        # Login
        response = await client.post("/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, sample_user_data):
        """Test login with wrong password"""
        # Register first
        await client.post("/auth/register", json=sample_user_data)
        
        # Login with wrong password
        response = await client.post("/auth/login", json={
            "email": sample_user_data["email"],
            "password": "WrongPassword@123"
        })
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user"""
        response = await client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Test@123456"
        })
        assert response.status_code == 401


class TestTokenRefresh:
    """Tests for token refresh"""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, sample_user_data):
        """Test successful token refresh"""
        # Register and login
        await client.post("/auth/register", json=sample_user_data)
        login_response = await client.post("/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh
        response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token"""
        response = await client.post("/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert response.status_code == 401

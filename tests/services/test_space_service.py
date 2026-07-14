import pytest
import pytest_asyncio
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.space_service import SpaceService
from app.models.space import Space, ListingType, ListingPricingMode
from app.models.category import Category
from app.models.user import User

@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession) -> User:
    user = User(
        email="host@test.com", 
        full_name="Host Test", 
        hashed_password="hashed",
        is_host=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def sample_category(db_session: AsyncSession) -> Category:
    cat = Category(
        name="Test Category",
        slug="test-category",
        listing_type=ListingType.SPACE
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat

@pytest.mark.asyncio
async def test_search_spaces_by_query(db_session: AsyncSession, sample_user: User, sample_category: Category):
    # Setup test spaces
    space1 = Space(
        host_id=sample_user.id,
        category_id=sample_category.id,
        title="Piscina Limpa",
        description="Uma piscina muito legal e limpa",
        address_line="Rua 1", city="Sao Paulo", state="SP", zip_code="000", neighborhood="Centro",
        price=100.0,
        is_active=True,
        is_approved=True
    )
    space2 = Space(
        host_id=sample_user.id,
        category_id=sample_category.id,
        title="Quadra de Tenis",
        description="Quadra de saibro rápida",
        address_line="Rua 2", city="Rio de Janeiro", state="RJ", zip_code="000", neighborhood="Copacabana",
        price=150.0,
        is_active=True,
        is_approved=True
    )
    db_session.add(space1)
    db_session.add(space2)
    await db_session.commit()

    service = SpaceService(db_session)
    
    # Test search by title
    results = await service.list_spaces(search_query="piscina")
    assert len(results) == 1
    assert results[0].title == "Piscina Limpa"

    # Test search by city
    results = await service.list_spaces(search_query="rio")
    assert len(results) == 1
    assert results[0].title == "Quadra de Tenis"

    # Test search no results
    results = await service.list_spaces(search_query="churrasqueira")
    assert len(results) == 0

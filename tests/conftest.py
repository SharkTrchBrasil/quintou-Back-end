"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient

from app.main import create_app
from app.database import Base, get_db
from app.config import settings

# Use banco de teste
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/quintou", "/quintou_test")

# Engine de teste
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    Rolls back all changes after the test.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with database session override
    """
    app = create_app()
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "Test@123456",
        "phone": "11987654321",
        "cpf": "12345678909",
        "is_host": False
    }


@pytest.fixture
def sample_host_data():
    """Sample host data for tests"""
    return {
        "email": "host@example.com",
        "full_name": "Test Host",
        "password": "Host@123456",
        "phone": "11987654322",
        "cpf": "98765432100",
        "is_host": True
    }


@pytest.fixture
def sample_space_data():
    """Sample space data for tests"""
    return {
        "title": "Piscina Maravilhosa",
        "description": "Linda piscina para festas",
        "category_id": "uuid-here",
        "address_line": "Rua Teste, 123",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01234-567",
        "neighborhood": "Centro",
        "price": 100.00,
        "max_guests": 20,
        "min_hours": 2,
        "max_hours": 8,
    }

@pytest.fixture
def sample_booking_data():
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "start_time": (now + datetime.timedelta(days=1)).isoformat(),
        "end_time": (now + datetime.timedelta(days=1, hours=4)).isoformat(),
        "guest_count": 10,
        "total_price": 400.0,
    }

@pytest.fixture
async def test_user(db_session, sample_user_data):
    from app.services.auth_service import AuthService
    from app.schemas.auth import UserCreate
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(UserCreate(**sample_user_data))
    return user

@pytest.fixture
async def auth_client(client, test_user, db_session):
    from app.services.auth_service import AuthService
    auth_service = AuthService(db_session)
    token = await auth_service.create_access_token(test_user.id)
    client.headers.update({"Authorization": f"Bearer {token.access_token}"})
    return client

@pytest.fixture
async def test_host(db_session, sample_host_data):
    from app.services.auth_service import AuthService
    from app.schemas.auth import UserCreate
    auth_service = AuthService(db_session)
    host = await auth_service.register_user(UserCreate(**sample_host_data))
    host.is_host = True
    await db_session.commit()
    return host

@pytest.fixture
async def host_client(client, test_host, db_session):
    from app.services.auth_service import AuthService
    auth_service = AuthService(db_session)
    token = await auth_service.create_access_token(test_host.id)
    # create a new client instance for host
    from httpx import AsyncClient
    from app.main import create_app
    from app.database import get_db
    app = create_app()
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    ac = AsyncClient(app=app, base_url="http://test")
    ac.headers.update({"Authorization": f"Bearer {token.access_token}"})
    return ac

@pytest.fixture(autouse=True)
def mock_stripe(monkeypatch):
    """Mock Stripe API globally"""
    class MockStripe:
        api_key = "sk_test_mock"
        
        class Account:
            @staticmethod
            async def create_async(**kwargs):
                return {"id": "acct_mock123", "type": "express"}
            @staticmethod
            async def retrieve_async(*args, **kwargs):
                return {"id": "acct_mock123", "payouts_enabled": True, "details_submitted": True}

        class AccountLink:
            @staticmethod
            async def create_async(**kwargs):
                return {"url": "https://connect.stripe.com/setup/s/mock"}

        class PaymentIntent:
            @staticmethod
            async def create_async(**kwargs):
                return {"id": "pi_mock123", "client_secret": "pi_mock123_secret_mock"}
            @staticmethod
            async def retrieve_async(intent_id, **kwargs):
                return {"id": intent_id, "status": "succeeded", "amount_received": 10000}
            @staticmethod
            async def capture_async(intent_id, **kwargs):
                return {"id": intent_id, "status": "succeeded"}
            @staticmethod
            async def cancel_async(intent_id, **kwargs):
                return {"id": intent_id, "status": "canceled"}
                
        class Transfer:
            @staticmethod
            async def create_async(**kwargs):
                return {"id": "tr_mock123"}
                
        class Refund:
            @staticmethod
            async def create_async(**kwargs):
                return {"id": "re_mock123"}
                
        class Event:
            @staticmethod
            def construct_from(data, key):
                return data

        class Webhook:
            @staticmethod
            def construct_event(payload, sig_header, secret):
                import json
                return json.loads(payload)

    monkeypatch.setattr("stripe.Account", MockStripe.Account)
    monkeypatch.setattr("stripe.AccountLink", MockStripe.AccountLink)
    monkeypatch.setattr("stripe.PaymentIntent", MockStripe.PaymentIntent)
    monkeypatch.setattr("stripe.Transfer", MockStripe.Transfer)
    monkeypatch.setattr("stripe.Refund", MockStripe.Refund)
    monkeypatch.setattr("stripe.Event", MockStripe.Event)
    monkeypatch.setattr("stripe.Webhook", MockStripe.Webhook)

@pytest.fixture(autouse=True)
def mock_s3(monkeypatch):
    """Mock AWS S3 client globally"""
    class MockS3Client:
        def upload_fileobj(self, *args, **kwargs):
            pass
            
    class MockBoto3:
        @staticmethod
        def client(*args, **kwargs):
            return MockS3Client()
            
    monkeypatch.setattr("boto3.client", MockBoto3.client)

@pytest.fixture(autouse=True)
def mock_firebase(monkeypatch):
    """Mock FirebaseService globally"""
    class MockFirebaseService:
        @staticmethod
        def send_push_notification(*args, **kwargs):
            pass
            
    monkeypatch.setattr("app.services.firebase_service.FirebaseService.send_push_notification", MockFirebaseService.send_push_notification)

@pytest.fixture(autouse=True)
def mock_celery(monkeypatch):
    """Mock Celery tasks globally"""
    class MockTask:
        @staticmethod
        def apply_async(*args, **kwargs):
            class AsyncResult:
                id = "mock_task_id"
            return AsyncResult()
            
    monkeypatch.setattr("celery.Task.apply_async", MockTask.apply_async)

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.database import Base
# Import all models to ensure they are registered with Base
import app.models.user
import app.models.space
import app.models.category
import app.models.booking
import app.models.review
import app.models.chat
import app.models.payment

async def create_all_tables():
    engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"), echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables verified/created successfully!")

if __name__ == "__main__":
    asyncio.run(create_all_tables())

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def main():
    async with async_session() as session:
        await session.execute(text("UPDATE spaces SET latitude = -17.0864, longitude = -40.9328 WHERE latitude IS NULL;"))
        await session.commit()
        print("Updated missing coordinates in database!")

if __name__ == "__main__":
    asyncio.run(main())

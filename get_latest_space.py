import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config import settings
import json

engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def main():
    async with async_session() as session:
        result = await session.execute(text("SELECT * FROM spaces ORDER BY created_at DESC LIMIT 1;"))
        row = result.mappings().first()
        if row:
            print("LATEST SPACE RECORD:")
            for key, value in row.items():
                print(f"{key}: {value}")
        else:
            print("No spaces found in the database.")

if __name__ == "__main__":
    asyncio.run(main())

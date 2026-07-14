import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from uuid import uuid4

DATABASE_URL = 'postgresql+asyncpg://postgres:kGTVCdBwYwJ1Fet4BVYpX65tJxfwkx3ZnArkP2E3RpXypEPcVJuUutEUBw2c7gwE@207.180.251.156:5431/postgres'
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with async_session() as session:
        # Insert a Space category
        await session.execute(text(
            """
            INSERT INTO categories (id, name, slug, icon, listing_type, requires_address_proof, is_active, created_at, updated_at)
            VALUES (:id, 'Salão de Festas', 'salao-de-festas', 'celebration', 'SPACE', true, true, now(), now())
            ON CONFLICT DO NOTHING
            """
        ), {'id': uuid4()})
        
        # Insert an Equipment category
        await session.execute(text(
            """
            INSERT INTO categories (id, name, slug, icon, listing_type, requires_address_proof, is_active, created_at, updated_at)
            VALUES (:id, 'Brinquedos', 'brinquedos', 'toys', 'EQUIPMENT', false, true, now(), now())
            ON CONFLICT DO NOTHING
            """
        ), {'id': uuid4()})
        await session.commit()
        print('Categories seeded!')

asyncio.run(seed())

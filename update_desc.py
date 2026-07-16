import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:kGTVCdBwYwJ1Fet4BVYpX65tJxfwkx3ZnArkP2E3RpXypEPcVJuUutEUBw2c7gwE@207.180.251.156:5431/postgres")
    async with engine.connect() as conn:
        await conn.execute(text("UPDATE categories SET description = 'Ideal para casamentos e grandes eventos' WHERE slug = 'salao-de-festas'"))
        await conn.execute(text("UPDATE categories SET description = 'Pula-pula, piscina de bolinhas, etc.' WHERE slug = 'brinquedos'"))
        await conn.commit()
        print("Descriptions updated!")

asyncio.run(main())

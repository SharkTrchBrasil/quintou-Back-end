import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:kGTVCdBwYwJ1Fet4BVYpX65tJxfwkx3ZnArkP2E3RpXypEPcVJuUutEUBw2c7gwE@207.180.251.156:5431/postgres")
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name, icon FROM categories WHERE name IN ('Salão de Festas', 'Brinquedos')"))
        for row in result:
            print(f"{row[0]} -> {row[1]}")
asyncio.run(main())

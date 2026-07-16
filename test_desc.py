import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:kGTVCdBwYwJ1Fet4BVYpX65tJxfwkx3ZnArkP2E3RpXypEPcVJuUutEUBw2c7gwE@207.180.251.156:5431/postgres")
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name, description FROM categories"))
        for row in result:
            desc = row[1] if row[1] else 'NULL'
            print(f"{row[0]}: {desc}")
asyncio.run(main())

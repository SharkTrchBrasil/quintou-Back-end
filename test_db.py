import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:kGTVCdBwYwJ1Fet4BVYpX65tJxfwkx3ZnArkP2E3RpXypEPcVJuUutEUBw2c7gwE@207.180.251.156:5431/postgres")
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT email, full_name FROM users WHERE email='csatrabalho3@gmail.com'"))
        for row in result:
            print(f"Email: {row[0]}, Name: {row[1]}")
asyncio.run(main())

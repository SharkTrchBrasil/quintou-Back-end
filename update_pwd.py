import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
new_hash = pwd_context.hash('Alpha2019@')

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:kGTVCdBwYwJ1Fet4BVYpX65tJxfwkx3ZnArkP2E3RpXypEPcVJuUutEUBw2c7gwE@207.180.251.156:5431/postgres")
    async with engine.connect() as conn:
        await conn.execute(text(f"UPDATE users SET hashed_password = '{new_hash}' WHERE email = 'csatrabalho1@gmail.com'"))
        await conn.execute(text(f"UPDATE users SET hashed_password = '{new_hash}' WHERE email = 'csatrabalho3@gmail.com'"))
        await conn.commit()
        print("Passwords updated!")

asyncio.run(main())

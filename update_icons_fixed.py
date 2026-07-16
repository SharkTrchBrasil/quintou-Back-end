# -*- coding: utf-8 -*-
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:kGTVCdBwYwJ1Fet4BVYpX65tJxfwkx3ZnArkP2E3RpXypEPcVJuUutEUBw2c7gwE@207.180.251.156:5431/postgres")
    async with engine.connect() as conn:
        # Use python's chr() to get unicode characters safely without relying on file encoding
        celebration_emoji = chr(0x1F389) # 🎉
        toys_emoji = chr(0x1F9F8) # 🧸
        
        # update by slug or previous garbled name
        await conn.execute(text("UPDATE categories SET icon = :icon1 WHERE slug = 'salao-de-festas'"), {"icon1": celebration_emoji})
        await conn.execute(text("UPDATE categories SET icon = :icon2 WHERE slug = 'brinquedos'"), {"icon2": toys_emoji})
        await conn.commit()
        
        # Verify
        result = await conn.execute(text("SELECT slug, icon FROM categories WHERE slug IN ('salao-de-festas', 'brinquedos')"))
        for row in result:
            print(f"{row[0]} -> {row[1].encode('unicode_escape').decode('utf-8')}")

asyncio.run(main())

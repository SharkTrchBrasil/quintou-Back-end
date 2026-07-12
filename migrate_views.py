import asyncio
import asyncpg

async def run():
    conn = await asyncpg.connect('postgresql://postgres:kGTVCdBwYwJ1Fet4BVYpX65tJxfwkx3ZnArkP2E3RpXypEPcVJuUutEUBw2c7gwE@207.180.251.156:5431/postgres')
    await conn.execute('ALTER TABLE spaces ADD COLUMN IF NOT EXISTS total_views INTEGER DEFAULT 0')
    print('Column total_views added successfully')
    await conn.close()

asyncio.run(run())

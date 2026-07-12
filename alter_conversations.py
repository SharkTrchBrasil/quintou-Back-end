import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return
        
    db_url = db_url.replace("postgresql+asyncpg://", "postgres://")

    print(f"Connecting to DB...")
    conn = await asyncpg.connect(db_url)
    try:
        print("Adding last_message_preview...")
        await conn.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS last_message_preview TEXT;")
        print("Adding host_unread_count...")
        await conn.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS host_unread_count INTEGER DEFAULT 0;")
        print("Adding guest_unread_count...")
        await conn.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS guest_unread_count INTEGER DEFAULT 0;")
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

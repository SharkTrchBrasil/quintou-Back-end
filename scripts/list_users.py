import asyncio
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User

async def list_users():
    async for db in get_db():
        try:
            stmt = select(User)
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            print(f"Total users: {len(users)}")
            print("-" * 50)
            for u in users:
                print(f"ID: {u.id}")
                print(f"Name: {getattr(u, 'full_name', 'N/A')}")
                print(f"Email: {getattr(u, 'email', 'N/A')}")
                print(f"Phone: {getattr(u, 'phone_number', 'N/A')}")
                print(f"Last Access: {getattr(u, 'last_access', 'N/A')}")
                print("-" * 50)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            break

if __name__ == "__main__":
    asyncio.run(list_users())

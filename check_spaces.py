import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.models.space import Space
from app.models.user import User
from app.models.category import Category
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def main():
    async with AsyncSessionLocal() as session:
        # Fetch the last 5 spaces created
        query = select(Space).order_by(Space.created_at.desc()).limit(5)
        result = await session.execute(query)
        spaces = result.scalars().all()
        
        print(f"Encontrei {len(spaces)} espaços recentes no banco:\n")
        for s in spaces:
            # fetch user
            user_res = await session.execute(select(User).where(User.id == s.host_id))
            user = user_res.scalars().first()
            # fetch category
            cat_res = await session.execute(select(Category).where(Category.id == s.category_id))
            cat = cat_res.scalars().first()
            
            print(f"- ID: {s.id}")
            print(f"  Título: {s.title}")
            print(f"  Dono: {user.full_name if user else s.owner_id}")
            print(f"  Categoria: {cat.name if cat else s.category_id}")
            print(f"  Status: {s.status.name if hasattr(s.status, 'name') else s.status}")
            print(f"  Criado em: {s.created_at}")
            print("-" * 30)

asyncio.run(main())

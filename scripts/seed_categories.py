import asyncio
import json
from sqlalchemy.future import select
from app.database import get_db, engine
from app.models.category import Category

categories_data = [
  {
    "slug": "churrasqueira-gourmet",
    "name": "Churrasqueiras e Gourmet",
    "icon": "🍖",
    "is_active": True
  },
  {
    "slug": "piscinas",
    "name": "Piscinas Privativas",
    "icon": "🏊",
    "is_active": True
  },
  {
    "slug": "quadras-areia",
    "name": "Quadras de Areia",
    "icon": "🏖️",
    "is_active": True
  },
  {
    "slug": "chacaras-day-use",
    "name": "Chácaras e Day Use",
    "icon": "🌳",
    "is_active": True
  },
  {
    "slug": "rooftops",
    "name": "Rooftops e Terraços",
    "icon": "🌆",
    "is_active": True
  },
  {
    "slug": "quadras-esportivas",
    "name": "Campos e Quadras",
    "icon": "⚽",
    "is_active": True
  },
  {
    "slug": "estudios",
    "name": "Estúdios e Criação",
    "icon": "🎙️",
    "is_active": True
  },
  {
    "slug": "saloes-festas",
    "name": "Salões de Festas",
    "icon": "🎉",
    "is_active": True
  },
  {
    "slug": "embarcacoes",
    "name": "Barcos e Lanchas",
    "icon": "🛥️",
    "is_active": True
  },
  {
    "slug": "espacos-zen",
    "name": "Espaços Zen",
    "icon": "🧘",
    "is_active": True
  }
]

async def seed():
    async for db in get_db():
        try:
            for idx, cat_data in enumerate(categories_data):
                stmt = select(Category).where(Category.slug == cat_data['slug'])
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"Skipping '{cat_data['name']}' (already exists).")
                else:
                    new_category = Category(
                        slug=cat_data['slug'],
                        name=cat_data['name'],
                        icon=cat_data['icon'],
                        is_active=cat_data['is_active'],
                        order=idx
                    )
                    db.add(new_category)
                    print(f"Added '{cat_data['name']}'.")
            
            await db.commit()
            print("Successfully added all new categories.")
        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")
            raise
        finally:
            break

if __name__ == "__main__":
    asyncio.run(seed())

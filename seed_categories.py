import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config import settings

# Engine setup
engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"), echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

categories = [
    {"name": "Piscinas", "slug": "piscinas", "icon": "pool", "listing_type": "SPACE", "order": 1},
    {"name": "Chácaras", "slug": "chacaras", "icon": "nature_people", "listing_type": "SPACE", "order": 2},
    {"name": "Salões de Festa", "slug": "saloes", "icon": "celebration", "listing_type": "SPACE", "order": 3},
    {"name": "Churrasqueiras", "slug": "churrasqueiras", "icon": "outdoor_grill", "listing_type": "SPACE", "order": 4},
    {"name": "Quadras", "slug": "quadras", "icon": "sports_tennis", "listing_type": "SPACE", "order": 5},
    {"name": "Estúdios", "slug": "estudios", "icon": "camera_alt", "listing_type": "SPACE", "order": 6},
    {"name": "Brinquedos", "slug": "brinquedos", "icon": "toys", "listing_type": "EQUIPMENT", "order": 7},
    {"name": "Mesas e Cadeiras", "slug": "mesas-cadeiras", "icon": "chair", "listing_type": "EQUIPMENT", "order": 8},
]

async def seed():
    async with async_session() as session:
        # Create categories table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS categories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR NOT NULL UNIQUE,
                slug VARCHAR NOT NULL UNIQUE,
                icon VARCHAR NOT NULL,
                listing_type VARCHAR NOT NULL,
                "order" INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        
        # Insert categories
        for cat in categories:
            await session.execute(text("""
                INSERT INTO categories (name, slug, icon, listing_type, "order")
                VALUES (:name, :slug, :icon, :listing_type, :order)
                ON CONFLICT (slug) DO NOTHING;
            """), cat)

        # Update spaces table
        # 1. Add category_id column if not exists
        await session.execute(text("""
            ALTER TABLE spaces ADD COLUMN IF NOT EXISTS category_id UUID;
        """))
        
        # 2. Map existing category enum to category_id
        await session.execute(text("""
            UPDATE spaces s
            SET category_id = c.id
            FROM categories c
            WHERE s.category_id IS NULL 
              AND (
                  (s.category = 'PISCINA' AND c.slug = 'piscinas') OR
                  (s.category = 'SITIO' AND c.slug = 'chacaras') OR
                  (s.category = 'SALAO_FESTAS' AND c.slug = 'saloes') OR
                  (s.category = 'CHURRASQUEIRA' AND c.slug = 'churrasqueiras') OR
                  (s.category = 'QUADRA' AND c.slug = 'quadras') OR
                  (s.category = 'ESTUDIO' AND c.slug = 'estudios') OR
                  (s.category = 'BRINQUEDOS' AND c.slug = 'brinquedos') OR
                  (s.category = 'MOBILIARIO' AND c.slug = 'mesas-cadeiras')
              );
        """))

        # Fallback for spaces without category_id (set to pool)
        await session.execute(text("""
            UPDATE spaces s
            SET category_id = (SELECT id FROM categories WHERE slug = 'piscinas')
            WHERE s.category_id IS NULL;
        """))
        
        # Add foreign key constraint
        # Need to wrap this in DO block for IF NOT EXISTS
        await session.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'fk_spaces_category'
                ) THEN
                    ALTER TABLE spaces
                    ADD CONSTRAINT fk_spaces_category
                    FOREIGN KEY (category_id) REFERENCES categories (id);
                END IF;
            END $$;
        """))
        
        # Drop old category column
        await session.execute(text("""
            ALTER TABLE spaces DROP COLUMN IF EXISTS category;
        """))
        
        await session.commit()
        print("Database schema updated and seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())

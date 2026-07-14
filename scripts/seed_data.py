"""
Script para popular banco de dados com dados iniciais
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_context
from app.models.category import Category
from app.models.user import User, UserRole
from app.utils.security import get_password_hash


async def seed_categories(db: AsyncSession):
    """Cria categorias padrão"""
    categories = [
        {"name": "Piscina", "icon": "🏊", "description": "Piscinas para festas e eventos"},
        {"name": "Quadra Esportiva", "icon": "⚽", "description": "Quadras de futebol, vôlei, tênis"},
        {"name": "Salão de Festas", "icon": "🎉", "description": "Salões para festas e eventos"},
        {"name": "Chácara", "icon": "🏡", "description": "Chácaras e sítios"},
        {"name": "Espaço Gourmet", "icon": "🍖", "description": "Churrasqueiras e espaços gourmet"},
        {"name": "Coworking", "icon": "💼", "description": "Espaços de trabalho compartilhado"},
        {"name": "Estúdio", "icon": "🎸", "description": "Estúdios de música, foto e vídeo"},
        {"name": "Equipamentos", "icon": "🎪", "description": "Pula-pula, mesas, cadeiras, etc"},
    ]
    
    print("Creating categories...")
    for cat_data in categories:
        category = Category(**cat_data)
        db.add(category)
    
    await db.commit()
    print(f"✅ Created {len(categories)} categories")


async def seed_admin_user(db: AsyncSession):
    """Cria usuário administrador padrão"""
    admin_email = "admin@quintou.com"
    
    # Verifica se admin já existe
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == admin_email))
    if result.scalars().first():
        print(f"⚠️  Admin user {admin_email} already exists")
        return
    
    admin = User(
        email=admin_email,
        full_name="Administrador Quintou",
        hashed_password=get_password_hash("Admin@123456"),
        role=UserRole.ADMIN,
        is_active=True,
        is_host=False,
        email_verified=True
    )
    
    db.add(admin)
    await db.commit()
    print(f"✅ Created admin user: {admin_email} / Admin@123456")
    print("⚠️  IMPORTANTE: Altere a senha do admin após o primeiro login!")


async def main():
    """Executa seed de dados"""
    print("=" * 60)
    print("QUINTOU - Database Seeder")
    print("=" * 60)
    
    async with get_db_context() as db:
        try:
            await seed_categories(db)
            await seed_admin_user(db)
            
            print("=" * 60)
            print("✅ Database seeded successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())

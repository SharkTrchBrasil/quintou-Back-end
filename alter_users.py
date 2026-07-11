import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings

async def alter_users_table():
    engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"), echo=True)
    async with engine.begin() as conn:
        # Check if columns exist, if not, add them
        columns = [
            ("email_verified", "BOOLEAN DEFAULT FALSE"),
            ("phone_verified", "BOOLEAN DEFAULT FALSE"),
            ("document_type", "VARCHAR"),
            ("document_url", "VARCHAR"),
            ("selfie_url", "VARCHAR"),
            ("kyc_status", "VARCHAR DEFAULT 'PENDING'"),
            ("kyc_verified_at", "TIMESTAMP WITH TIME ZONE"),
            ("is_verified_host", "BOOLEAN DEFAULT FALSE"),
            ("is_pro_host", "BOOLEAN DEFAULT FALSE"),
            ("hosting_since", "TIMESTAMP WITH TIME ZONE"),
            ("avg_response_time_minutes", "INTEGER"),
            ("stripe_account_id", "VARCHAR"),
            ("stripe_customer_id", "VARCHAR"),
            ("stripe_account_status", "VARCHAR DEFAULT 'pending'"),
            ("stripe_onboarding_complete", "BOOLEAN DEFAULT FALSE")
        ]
        
        for col_name, col_type in columns:
            try:
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                print(f"Added column {col_name}")
            except Exception as e:
                print(f"Failed to add column {col_name}: {e}")

if __name__ == "__main__":
    asyncio.run(alter_users_table())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text
from app.core.config import settings
from app.models import Base
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Float
from pgvector.sqlalchemy import Vector

# Create async engine without connection pooling
engine = create_async_engine(
    settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=True,
    poolclass=NullPool
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    async with engine.begin() as conn:
        # Ensure pgvector extension is created
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Register vector type with SQLAlchemy
        from sqlalchemy.dialects import postgresql
        postgresql.base.ischema_names['vector'] = Vector
        # Create tables
        await conn.run_sync(Base.metadata.create_all)

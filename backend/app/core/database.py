"""
Database configuration and session management.
Supports both sync and async PostgreSQL connections.
"""

import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_database_url():
    """Get database URL from environment."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/empeff"
    )


def get_debug_mode():
    """Get debug mode from environment."""
    return os.getenv("DEBUG", "False").lower() == "true"


# ============================================================================
# SYNC DATABASE (for backward compatibility)
# ============================================================================

def get_sync_engine():
    """
    Create synchronous database engine.
    
    Uses psycopg2-binary driver (postgresql://).
    """
    database_url = get_database_url()
    debug_mode = get_debug_mode()
    
    engine = create_engine(
        database_url,
        echo=debug_mode,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    
    return engine


# Create sync engine
engine = get_sync_engine()


def create_db_and_tables():
    """
    Create all database tables.
    
    Note: For production, use Alembic migrations instead.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    FastAPI dependency for sync database session.
    
    Usage:
        from sqlmodel import Session
        from app.core.database import get_session
        
        @router.get("/items")
        def get_items(session: Session = Depends(get_session)):
            items = session.exec(select(Item)).all()
            return items
    """
    with Session(engine) as session:
        yield session


# ============================================================================
# ASYNC DATABASE (for async routes with validation engine)
# ============================================================================

def get_async_database_url():
    """
    Get async database URL.
    
    Converts postgresql:// to postgresql+asyncpg:// for async support.
    """
    database_url = get_database_url()
    
    # Replace driver for async support
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    return database_url


def get_async_engine():
    """
    Create asynchronous database engine.
    
    Uses asyncpg driver (postgresql+asyncpg://).
    """
    async_database_url = get_async_database_url()
    debug_mode = get_debug_mode()
    
    engine = create_async_engine(
        async_database_url,
        echo=debug_mode,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    
    return engine


# Create async engine
async_engine = get_async_engine()

# Create async session factory
async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session():
    """
    FastAPI dependency for async database session.
    
    Usage:
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.core.database import get_async_session
        
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_async_session)):
            result = await session.execute(select(Item))
            items = result.scalars().all()
            return items
    """
    async with async_session_maker() as session:
        yield session

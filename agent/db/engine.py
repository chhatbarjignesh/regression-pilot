"""
Async SQLAlchemy engine, session factory, and lifespan helpers.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config.settings import settings
from agent.db.models import Base

logger = logging.getLogger(__name__)

# Engine — pool_pre_ping keeps connections healthy across restarts
engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables() -> None:
    """Create all tables. Called at app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("[db] Tables ready")


async def drop_tables() -> None:
    """Drop all tables. For testing only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_engine() -> None:
    """Dispose engine. Called at app shutdown."""
    await engine.dispose()
    logger.info("[db] Engine closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for a database session.
    Commits on clean exit, rolls back on exception.

    Usage:
        async with get_session() as session:
            session.add(obj)
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

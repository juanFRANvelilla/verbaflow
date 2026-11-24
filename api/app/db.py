from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.settings import get_settings


class Base(DeclarativeBase):
    pass


def _engine():
    return create_async_engine(
        get_settings().resolved_database_url,
        echo=get_settings().debug,
        pool_pre_ping=True,
    )


engine = _engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
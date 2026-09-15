from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def dispose_engine() -> None:
    """Drop all pooled connections.

    Each connection is bound to the asyncio event loop it was created on.
    Celery tasks that wrap their DB work in asyncio.run() get a brand new
    event loop per task, so a connection pooled from a previous task's loop
    is unusable and errors with "attached to a different loop". Call this
    at the end of every asyncio.run()-wrapped Celery task so the next task
    starts with a clean pool instead of a stale one.
    """
    await engine.dispose()

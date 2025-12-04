from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from app.core.config import settings

# For async operations (preferred)
async_url = settings.DATABASE_URL
if async_url.startswith("sqlite:///"):
    # SQLite async requires special handling
    async_url = async_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    async_engine = create_async_engine(
        async_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
elif async_url.startswith("postgresql://"):
    async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(async_url, echo=settings.DEBUG)
else:
    async_engine = create_async_engine(async_url, echo=settings.DEBUG)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# For sync operations (SQLAlchemy 2.0 style - used for table creation)
sync_url = settings.DATABASE_URL
if sync_url.startswith("sqlite:///"):
    sync_engine = create_engine(
        sync_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    # Enable foreign keys for SQLite
    @event.listens_for(sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
elif sync_url.startswith("postgresql://"):
    sync_url = sync_url.replace("postgresql://", "postgresql+psycopg2://")
    sync_engine = create_engine(sync_url, echo=settings.DEBUG)
else:
    sync_engine = create_engine(sync_url, echo=settings.DEBUG)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Base class for models
Base = declarative_base()


# Dependency to get DB session (async)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Sync DB session dependency (for compatibility)
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


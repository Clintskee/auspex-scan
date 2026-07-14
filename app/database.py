"""Database engine, schema base, and session dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./auspex_scan.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy database models."""

    pass


def create_database() -> None:
    """Create tables that do not already exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Provide one database session for a request and close it afterward."""
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()

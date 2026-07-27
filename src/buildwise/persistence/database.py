from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from buildwise.config.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    connect_args = (
        {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    )
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def check_database_connection() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return the shared SQLAlchemy session factory."""

    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def initialize_database() -> None:
    """Create the minimal BuildWise persistence schema."""

    from buildwise.persistence.models import Base

    Base.metadata.create_all(get_engine())

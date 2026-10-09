"""
Database connection, session management, and Base definition.
Compatible with SQLite (local development and offline demo) and PostgreSQL / Supabase.
"""

import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif settings.database_url.startswith(("postgresql+psycopg", "postgresql", "postgres")):
    # Supabase's transaction-mode pooler multiplexes server connections, which
    # breaks psycopg's cached prepared statements ("prepared statement already
    # exists"). Sending statements unprepared keeps routing across the pooler.
    connect_args = {"prepare_threshold": None}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency yield for FastAPI request lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    """
    Creates missing tables and adds missing columns to existing tables.
    Additive only: never drops or alters existing columns, so existing data is preserved.
    """
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                col_type = column.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'))
                logger.info("Added missing column %s.%s", table.name, column.name)

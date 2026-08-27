"""
SQLAlchemy engine, session factory, and declarative base.

DATABASE_URL controls where data lives:
  - Local dev default: sqlite:///./rexplore.db (fine for local work, but
    NEVER durable in production - Render's filesystem is ephemeral, so a
    SQLite file there is wiped on every redeploy, taking every user account
    and all their history with it).
  - Production: set DATABASE_URL to a Render PostgreSQL connection string.
    Postgres lives on its own persistent service, independent of the web
    service's filesystem, so accounts/history survive redeploys, restarts,
    and scaling exactly as they should.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

settings = get_settings()

is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    # pool_pre_ping: cheap "is this connection still alive" check before
    # each checkout. Cloud Postgres providers (including Render) can close
    # idle connections server-side; without this, the *next* query on a
    # stale connection fails outright instead of transparently reconnecting.
    # Harmless no-op overhead for SQLite.
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create any tables that don't exist yet. Called once at startup.

    This is intentionally additive only: create_all() never drops or
    recreates a table that's already there, and never touches existing
    rows. It's safe to run on every startup against a database that
    already has real user data in it.
    """
    # Import models so they register on Base.metadata before create_all.
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

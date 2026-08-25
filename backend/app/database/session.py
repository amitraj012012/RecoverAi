import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Resolve SQLite database path to an absolute path in the workspace root
raw_db_url = settings.DATABASE_URL or "sqlite:///./recoverai.db"

if raw_db_url.startswith("sqlite:///./") or raw_db_url == "sqlite:///recoverai.db":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    db_path = os.path.join(base_dir, "recoverai.db")
    raw_db_url = f"sqlite:///{db_path}"

connect_args = {}
if raw_db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    raw_db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI database dependency providing a transactional session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes all database tables."""
    # Import all models before create_all
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

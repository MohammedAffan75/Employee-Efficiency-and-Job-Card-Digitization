from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = create_engine(settings.database_url, echo=True)


def create_db_and_tables():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency for getting database session."""
    with Session(engine) as session:
        yield session

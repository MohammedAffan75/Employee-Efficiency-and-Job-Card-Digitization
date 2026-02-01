"""
Create database tables directly using SQLModel.
"""
from sqlmodel import SQLModel, create_engine
from app.core.config import settings
from app.models.models import *  # This imports all models

# Create engine
engine = create_engine(settings.database_url)

def create_tables():
    """Create all tables in database."""
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("✅ Tables created successfully!")

if __name__ == "__main__":
    create_tables()
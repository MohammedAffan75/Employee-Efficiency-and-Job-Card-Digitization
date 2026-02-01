#!/usr/bin/env python3
"""
Create a simple SQLite database for testing
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlmodel import SQLModel, create_engine, Session
from app.models.models import *  # Import all models

# Create SQLite database
DATABASE_URL = "sqlite:///./backend/test.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_tables():
    """Create all tables"""
    print("Creating tables...")
    SQLModel.metadata.create_all(engine)
    print("✅ Tables created successfully!")

def create_sample_data():
    """Create sample data"""
    print("Creating sample data...")
    
    with Session(engine) as session:
        # Create sample activity codes
        activity1 = ActivityCode(
            code="SETUP",
            description="Machine Setup",
            std_hours_per_unit=0.5,
            efficiency_type=EfficiencyTypeEnum.TIME_BASED,
            last_updated=datetime.utcnow()
        )
        
        activity2 = ActivityCode(
            code="PROD",
            description="Production",
            std_qty_per_hour=10.0,
            efficiency_type=EfficiencyTypeEnum.QUANTITY_BASED,
            last_updated=datetime.utcnow()
        )
        
        session.add(activity1)
        session.add(activity2)
        
        # Create sample machines
        machine1 = Machine(
            machine_code="M001",
            description="CNC Machine 1",
            work_center="WC01"
        )
        
        machine2 = Machine(
            machine_code="M002",
            description="Lathe Machine 1",
            work_center="WC02"
        )
        
        session.add(machine1)
        session.add(machine2)
        
        session.commit()
        print("✅ Sample data created successfully!")

if __name__ == "__main__":
    create_tables()
    create_sample_data()
    print("🎉 Database setup complete!")
    print(f"Database file: {DATABASE_URL}")
"""
Reset Database Script
Drops all tables and recreates them with new schema.
"""
from sqlmodel import SQLModel
from app.database import engine
from app.models.employee import Employee

def reset_database():
    """Drop all tables and recreate them."""
    print("🔄 Resetting database...")
    
    # Use raw SQL to drop everything with CASCADE
    print("Dropping all tables and types with CASCADE...")
    with engine.begin() as conn:
        # Drop all tables that might exist (old and new)
        conn.exec_driver_sql("DROP TABLE IF EXISTS employees CASCADE")
        conn.exec_driver_sql("DROP TABLE IF EXISTS efficiency_employees CASCADE")
        conn.exec_driver_sql("DROP TABLE IF EXISTS job_cards CASCADE")
        conn.exec_driver_sql("DROP TABLE IF EXISTS validation_flags CASCADE")
        conn.exec_driver_sql("DROP TABLE IF EXISTS activity_codes CASCADE")
        conn.exec_driver_sql("DROP TABLE IF EXISTS machines CASCADE")
        conn.exec_driver_sql("DROP TABLE IF EXISTS work_orders CASCADE")
        
        # Now drop the enum type
        conn.exec_driver_sql("DROP TYPE IF EXISTS roleenum CASCADE")
        conn.exec_driver_sql("DROP TYPE IF EXISTS efficiencytypeenum CASCADE")
        conn.exec_driver_sql("DROP TYPE IF EXISTS flagtypeenum CASCADE")
    
    print("Creating all tables with new schema...")
    SQLModel.metadata.create_all(engine)
    print("✅ Database reset complete!")
    print("\n📝 Next steps:")
    print("   1. Start backend: uvicorn app.main:app --reload")
    print("   2. Go to http://localhost:8000/docs")
    print("   3. Create users with POST /employees")

if __name__ == "__main__":
    reset_database()

"""
Migrate employee data from efficiency_employees to employees table
Run this before running the Alembic migration.
"""
import asyncio
from sqlalchemy import text
from app.core.database import async_engine


async def migrate_employee_data():
    """Copy all data from efficiency_employees to employees table."""
    
    async with async_engine.begin() as conn:
        # Check if employees table exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'employees'
            )
        """))
        employees_table_exists = result.scalar()
        
        if not employees_table_exists:
            print("❌ Employees table doesn't exist yet. Creating it...")
            # This will be created by Alembic migration or models
            print("⚠️  Please ensure the Employee model is properly set up")
            return
        
        # Check if efficiency_employees table exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'efficiency_employees'
            )
        """))
        eff_emp_exists = result.scalar()
        
        if not eff_emp_exists:
            print("❌ efficiency_employees table doesn't exist")
            return
        
        print("✅ Both tables exist. Starting migration...")
        
        # Copy data from efficiency_employees to employees
        await conn.execute(text("""
            INSERT INTO employees (
                id, ec_number, name, role, team, join_date, hashed_password, is_active, created_at, updated_at
            )
            SELECT 
                id, 
                ec_number, 
                name, 
                role, 
                team, 
                join_date, 
                hashed_password,
                is_active,
                NOW(),
                NOW()
            FROM efficiency_employees
            ON CONFLICT (ec_number) DO UPDATE SET
                name = EXCLUDED.name,
                role = EXCLUDED.role,
                team = EXCLUDED.team,
                join_date = EXCLUDED.join_date,
                hashed_password = EXCLUDED.hashed_password,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
        """))
        
        # Get count
        result = await conn.execute(text("SELECT COUNT(*) FROM employees"))
        count = result.scalar()
        
        print(f"✅ Successfully migrated {count} employees to new table!")
        print("✅ You can now run: alembic upgrade head")


if __name__ == "__main__":
    print("=" * 60)
    print("Employee Data Migration Tool")
    print("=" * 60)
    asyncio.run(migrate_employee_data())

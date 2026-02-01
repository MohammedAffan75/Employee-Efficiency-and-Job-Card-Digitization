#!/usr/bin/env python3
"""
Setup test data for the backend
"""
import sys
import os
sys.path.append('backend')

from sqlmodel import Session, create_engine
from app.models.models import EfficiencyEmployee, RoleEnum, ActivityCode, Machine, EfficiencyTypeEnum
from app.core.security import hash_password
from datetime import date, datetime

# Use SQLite for testing
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_tables():
    """Create all tables"""
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    print("✅ Tables created")

def create_test_data():
    """Create test data"""
    with Session(engine) as session:
        # Create admin user
        admin = session.get(EfficiencyEmployee, 1)
        if not admin:
            admin = EfficiencyEmployee(
                ec_number="ADMIN001",
                name="Admin User",
                hashed_password=hash_password("admin123"),
                role=RoleEnum.ADMIN,
                team="Admin",
                join_date=date.today(),
                is_active=True
            )
            session.add(admin)
            print("✅ Created admin user: ADMIN001 / admin123")
        
        # Create supervisor user
        supervisor = EfficiencyEmployee(
            ec_number="SUP001",
            name="Supervisor User",
            hashed_password=hash_password("super123"),
            role=RoleEnum.SUPERVISOR,
            team="Production Team A",
            join_date=date.today(),
            is_active=True
        )
        session.add(supervisor)
        print("✅ Created supervisor user: SUP001 / super123")
        
        # Create operator user
        operator = EfficiencyEmployee(
            ec_number="OPR001",
            name="Operator User",
            hashed_password=hash_password("oper123"),
            role=RoleEnum.OPERATOR,
            team="Production Team A",
            join_date=date.today(),
            is_active=True
        )
        session.add(operator)
        print("✅ Created operator user: OPR001 / oper123")
        
        # Create sample activity codes
        activities = [
            ActivityCode(
                code="SETUP",
                description="Machine Setup",
                std_hours_per_unit=0.5,
                efficiency_type=EfficiencyTypeEnum.TIME_BASED,
                last_updated=datetime.utcnow()
            ),
            ActivityCode(
                code="PROD",
                description="Production",
                std_qty_per_hour=10.0,
                efficiency_type=EfficiencyTypeEnum.QUANTITY_BASED,
                last_updated=datetime.utcnow()
            ),
            ActivityCode(
                code="MAINT",
                description="Maintenance",
                std_hours_per_unit=1.0,
                efficiency_type=EfficiencyTypeEnum.TASK_BASED,
                last_updated=datetime.utcnow()
            )
        ]
        
        for activity in activities:
            session.add(activity)
        print("✅ Created sample activity codes")
        
        # Create sample machines
        machines = [
            Machine(
                machine_code="M001",
                description="CNC Machine 1",
                work_center="WC01"
            ),
            Machine(
                machine_code="M002",
                description="CNC Machine 2",
                work_center="WC01"
            ),
            Machine(
                machine_code="M003",
                description="Lathe Machine 1",
                work_center="WC02"
            )
        ]
        
        for machine in machines:
            session.add(machine)
        print("✅ Created sample machines")
        
        session.commit()
        print("✅ All test data created successfully!")

def main():
    print("🔧 Setting up test database...")
    create_tables()
    create_test_data()
    print("🎉 Setup complete!")
    print("\nTest credentials:")
    print("Admin: ADMIN001 / admin123")
    print("Supervisor: SUP001 / super123")
    print("Operator: OPR001 / oper123")

if __name__ == "__main__":
    main()
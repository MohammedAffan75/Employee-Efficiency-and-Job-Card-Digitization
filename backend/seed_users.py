"""
Seed script to create initial employees for testing.
Creates an admin, supervisor, and operator user with hashed passwords.

Run with: python seed_users.py
"""

from datetime import date
from sqlmodel import Session, select

from app.core.database import engine
from app.core.security import hash_password
from app.models.models import EfficiencyEmployee, RoleEnum


def create_seed_employees():
    """Create seed employees with different roles."""
    
    seed_data = [
        {
            "ec_number": "ADMIN001",
            "name": "Admin User",
            "password": "admin123",
            "role": RoleEnum.ADMIN,
            "team": "Management",
            "join_date": date(2024, 1, 1),
        },
        {
            "ec_number": "SUP001",
            "name": "Supervisor User",
            "password": "super123",
            "role": RoleEnum.SUPERVISOR,
            "team": "Production Team A",
            "join_date": date(2024, 2, 1),
        },
        {
            "ec_number": "OPR001",
            "name": "Operator User",
            "password": "oper123",
            "role": RoleEnum.OPERATOR,
            "team": "Production Team A",
            "join_date": date(2024, 3, 1),
        },
    ]
    
    with Session(engine) as session:
        for data in seed_data:
            # Check if employee already exists
            statement = select(EfficiencyEmployee).where(
                EfficiencyEmployee.ec_number == data["ec_number"]
            )
            existing = session.exec(statement).first()
            
            if existing:
                print(f"⚠️  Employee {data['ec_number']} already exists, skipping...")
                continue
            
            # Create new employee with hashed password
            password = data.pop("password")
            employee = EfficiencyEmployee(
                **data,
                hashed_password=hash_password(password),
                is_active=True
            )
            
            session.add(employee)
            print(f"✅ Created employee: {employee.ec_number} - {employee.name} ({employee.role.value})")
        
        session.commit()
        print("\n🎉 Seed data creation complete!")


def display_credentials():
    """Display the login credentials for testing."""
    print("\n" + "="*60)
    print("TEST CREDENTIALS")
    print("="*60)
    print("\n1. ADMIN User:")
    print("   EC Number: ADMIN001")
    print("   Password:  admin123")
    print("   Role:      ADMIN")
    
    print("\n2. SUPERVISOR User:")
    print("   EC Number: SUP001")
    print("   Password:  super123")
    print("   Role:      SUPERVISOR")
    
    print("\n3. OPERATOR User:")
    print("   EC Number: OPR001")
    print("   Password:  oper123")
    print("   Role:      OPERATOR")
    
    print("\n" + "="*60)
    print("Use these credentials to test the /api/auth/login endpoint")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("🌱 Starting seed data creation...\n")
    create_seed_employees()
    display_credentials()

"""Quick script to check recent job cards in the database"""
import asyncio
from sqlalchemy import select, desc
from app.core.database import async_engine
from app.models.models import JobCard
from sqlalchemy.ext.asyncio import AsyncSession


async def check_recent_jobcards():
    async with AsyncSession(async_engine) as session:
        # Get last 10 job cards
        statement = select(JobCard).order_by(desc(JobCard.id)).limit(10)
        result = await session.execute(statement)
        job_cards = result.scalars().all()
        
        print("=" * 80)
        print(f"Last 10 Job Cards in Database:")
        print("=" * 80)
        
        if not job_cards:
            print("❌ No job cards found in database!")
            return
        
        for jc in job_cards:
            print(f"\n📋 Job Card ID: {jc.id}")
            print(f"   Employee ID: {jc.employee_id}")
            print(f"   Supervisor ID: {jc.supervisor_id}")
            print(f"   Work Order ID: {jc.work_order_id}")
            print(f"   Machine ID: {jc.machine_id}")
            print(f"   Activity: {jc.activity_desc}")
            print(f"   Qty: {jc.qty}, Hours: {jc.actual_hours}")
            print(f"   Status: {jc.status}, Source: {jc.source}")
            print(f"   Entry Date: {jc.entry_date}")


if __name__ == "__main__":
    asyncio.run(check_recent_jobcards())

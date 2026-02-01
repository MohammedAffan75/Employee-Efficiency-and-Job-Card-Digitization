"""Check for TECHNICIAN source job cards"""
import asyncio
from sqlalchemy import select
from app.core.database import async_engine
from app.models.models import JobCard, SourceEnum
from sqlalchemy.ext.asyncio import AsyncSession


async def check_technician_jobcards():
    async with AsyncSession(async_engine) as session:
        # Get TECHNICIAN job cards
        statement = select(JobCard).where(JobCard.source == SourceEnum.TECHNICIAN)
        result = await session.execute(statement)
        job_cards = result.scalars().all()
        
        print("=" * 80)
        print(f"TECHNICIAN Job Cards (created by operators):")
        print("=" * 80)
        
        if not job_cards:
            print("❌ No TECHNICIAN job cards found!")
            print("\nThis means operators haven't successfully created any job cards yet.")
            print("Check the browser console for errors when creating a job card.")
            return
        
        print(f"\n✅ Found {len(job_cards)} TECHNICIAN job cards:\n")
        for jc in job_cards:
            print(f"📋 ID: {jc.id} | Employee: {jc.employee_id} | Date: {jc.entry_date} | Activity: {jc.activity_desc}")


if __name__ == "__main__":
    asyncio.run(check_technician_jobcards())

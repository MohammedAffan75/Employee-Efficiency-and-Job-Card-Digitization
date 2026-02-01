#!/usr/bin/env python
"""
CLI script for bulk importing jobcards from Excel/CSV files.

Usage:
    python scripts/import_jobcards.py <file_path> --supervisor-id=5

Example:
    python scripts/import_jobcards.py data/jobcards_october.xlsx --supervisor-id=5
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_database_url
from app.services.import_service import import_jobcards_from_file


async def main(file_path: str, supervisor_id: int):
    """
    Import jobcards from file using CLI.
    
    Args:
        file_path: Path to Excel or CSV file
        supervisor_id: ID of supervisor creating the jobcards
    """
    # Check file exists
    path = Path(file_path)
    if not path.exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    
    if not path.suffix in ('.csv', '.xlsx', '.xls'):
        print(f"❌ Error: Unsupported file type: {path.suffix}")
        print("   Supported types: .csv, .xlsx, .xls")
        sys.exit(1)
    
    # Read file
    print(f"📁 Reading file: {file_path}")
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    # Create async engine
    database_url = get_async_database_url()
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Process import
    print(f"🔄 Processing import with supervisor_id={supervisor_id}...")
    async with async_session_maker() as session:
        report = await import_jobcards_from_file(
            file_content=file_content,
            filename=path.name,
            supervisor_id=supervisor_id,
            session=session,
        )
    
    # Print report
    print("\n" + "="*60)
    print("📊 IMPORT REPORT")
    print("="*60)
    print(f"Total rows:     {report.total_rows}")
    print(f"✅ Accepted:    {report.accepted_count}")
    print(f"❌ Rejected:    {report.rejected_count}")
    print(f"⚠️  Flagged:     {report.flagged_count}")
    print("="*60)
    
    # Show rejected rows
    if report.rejected:
        print("\n❌ REJECTED ROWS:")
        print("-" * 60)
        for rej in report.rejected[:10]:  # Show first 10
            print(f"Row {rej.row_number}: {rej.reason}")
        if len(report.rejected) > 10:
            print(f"... and {len(report.rejected) - 10} more")
    
    # Show flagged jobcards
    if report.flagged:
        print("\n⚠️  FLAGGED JOBCARDS:")
        print("-" * 60)
        for flagged in report.flagged[:10]:  # Show first 10
            print(f"JobCard #{flagged.jobcard_id}: {', '.join(flagged.flags)}")
        if len(report.flagged) > 10:
            print(f"... and {len(report.flagged) - 10} more")
    
    print("\n✨ Import complete!")
    
    # Exit code based on success
    if report.rejected_count > 0:
        sys.exit(1)  # Partial failure
    else:
        sys.exit(0)  # Complete success


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Import jobcards from Excel or CSV file'
    )
    parser.add_argument(
        'file_path',
        help='Path to Excel (.xlsx, .xls) or CSV file'
    )
    parser.add_argument(
        '--supervisor-id',
        type=int,
        required=True,
        help='ID of supervisor creating the jobcards'
    )
    
    args = parser.parse_args()
    
    # Run async main
    asyncio.run(main(args.file_path, args.supervisor_id))

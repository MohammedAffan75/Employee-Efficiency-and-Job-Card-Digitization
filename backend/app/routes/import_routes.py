"""
Import routes for bulk jobcard imports.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import require_roles
from app.models.models import EfficiencyEmployee
from app.schemas.import_schemas import ImportReport
from app.services.import_service import import_jobcards_from_file

router = APIRouter()


@router.post("/jobcards", response_model=ImportReport)
async def import_jobcards(
    file: UploadFile = File(..., description="Excel (.xlsx, .xls) or CSV file"),
    session: AsyncSession = Depends(get_async_session),
    current_user: EfficiencyEmployee = Depends(require_roles(["SUPERVISOR", "ADMIN"])),
) -> ImportReport:
    """
    Import jobcards from Excel or CSV file.
    
    Expected columns:
    - ec_number: Employee EC number (required)
    - entry_date: Entry date YYYY-MM-DD or DD/MM/YYYY (required)
    - shift: Shift identifier (optional)
    - machine_code: Machine code (required)
    - wo_number: Work order number (required)
    - activity_code: Activity code (optional, can be empty for AWC)
    - activity_desc: Activity description (required)
    - qty: Quantity (required)
    - actual_hours: Actual hours (required)
    - status: C or IC (required)
    
    Returns:
        Import report with counts of accepted, rejected, and flagged records
    
    Access: SUPERVISOR or ADMIN only
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be .csv, .xlsx, or .xls format"
        )
    
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading file: {str(e)}"
        )
    
    # Process import
    report = await import_jobcards_from_file(
        file_content=file_content,
        filename=file.filename,
        supervisor_id=current_user.id,
        session=session,
    )
    
    return report

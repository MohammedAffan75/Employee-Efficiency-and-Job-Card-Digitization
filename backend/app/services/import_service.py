"""
Import service for bulk jobcard creation from Excel/CSV files.
"""

import io
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, date

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.models import (
    EfficiencyEmployee,
    Machine,
    WorkOrder,
    ActivityCode,
    JobCard,
    ValidationFlag,
    JobCardStatusEnum,
    SourceEnum,
)
from app.schemas.import_schemas import RejectedRow, FlaggedJobCard, ImportReport
from app.services.validation_engine import ValidationEngine


async def import_jobcards_from_file(
    file_content: bytes,
    filename: str,
    supervisor_id: int,
    session: AsyncSession,
) -> ImportReport:
    """
    Import jobcards from Excel or CSV file.
    
    Expected columns:
    - ec_number: Employee EC number
    - entry_date: Date (YYYY-MM-DD or DD/MM/YYYY)
    - shift: Optional shift identifier
    - machine_code: Machine code
    - wo_number: Work order number
    - activity_code: Activity code (optional, can be None/empty)
    - activity_desc: Activity description
    - qty: Quantity
    - actual_hours: Actual hours worked
    - status: C or IC
    
    Returns:
        ImportReport with accepted, rejected, and flagged counts
    """
    # Parse file
    try:
        df = _parse_file(file_content, filename)
    except Exception as e:
        return ImportReport(
            total_rows=0,
            accepted_count=0,
            rejected_count=1,
            flagged_count=0,
            rejected=[RejectedRow(row_number=0, data={}, reason=f"File parsing error: {str(e)}")],
        )
    
    # Validate required columns
    required_cols = ['ec_number', 'entry_date', 'machine_code', 'wo_number', 
                     'activity_desc', 'qty', 'actual_hours', 'status']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return ImportReport(
            total_rows=0,
            accepted_count=0,
            rejected_count=1,
            flagged_count=0,
            rejected=[RejectedRow(
                row_number=0,
                data={},
                reason=f"Missing required columns: {', '.join(missing_cols)}"
            )],
        )
    
    # Pre-load reference data
    employees_map = await _load_employees_map(session)
    machines_map = await _load_machines_map(session)
    work_orders_map = await _load_work_orders_map(session)
    activity_codes_map = await _load_activity_codes_map(session)
    
    # Process each row
    accepted_count = 0
    rejected: List[RejectedRow] = []
    flagged: List[FlaggedJobCard] = []
    
    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel row number (1-indexed + header)
        
        try:
            # Validate and map row
            jobcard_data, error = await _validate_and_map_row(
                row.to_dict(),
                row_num,
                employees_map,
                machines_map,
                work_orders_map,
                activity_codes_map,
            )
            
            if error:
                rejected.append(RejectedRow(
                    row_number=row_num,
                    data=row.to_dict(),
                    reason=error,
                ))
                continue
            
            # Create jobcard
            jobcard = JobCard(
                employee_id=jobcard_data['employee_id'],
                supervisor_id=supervisor_id,
                machine_id=jobcard_data['machine_id'],
                work_order_id=jobcard_data['work_order_id'],
                activity_code_id=jobcard_data.get('activity_code_id'),
                activity_desc=jobcard_data['activity_desc'],
                qty=jobcard_data['qty'],
                actual_hours=jobcard_data['actual_hours'],
                status=jobcard_data['status'],
                entry_date=jobcard_data['entry_date'],
                source=SourceEnum.SUPERVISOR,
            )
            
            session.add(jobcard)
            await session.flush()
            await session.refresh(jobcard)
            
            # Run validation engine
            engine = ValidationEngine()
            flags = await engine.run_for_jobcard(jobcard, session)
            
            accepted_count += 1
            
            # Track if flagged
            if flags:
                flagged.append(FlaggedJobCard(
                    jobcard_id=jobcard.id,
                    flags=[flag.flag_type.value for flag in flags],
                ))
        
        except Exception as e:
            rejected.append(RejectedRow(
                row_number=row_num,
                data=row.to_dict(),
                reason=f"Processing error: {str(e)}",
            ))
    
    # Commit all successful imports
    await session.commit()
    
    return ImportReport(
        total_rows=len(df),
        accepted_count=accepted_count,
        rejected_count=len(rejected),
        flagged_count=len(flagged),
        rejected=rejected,
        flagged=flagged,
    )


def _parse_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """Parse Excel or CSV file to DataFrame."""
    if filename.endswith('.csv'):
        return pd.read_csv(io.BytesIO(file_content))
    elif filename.endswith(('.xlsx', '.xls')):
        return pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
    else:
        raise ValueError(f"Unsupported file type: {filename}. Use .csv, .xlsx, or .xls")


async def _load_employees_map(session: AsyncSession) -> Dict[str, int]:
    """Load all employees into a map: ec_number -> id"""
    stmt = select(EfficiencyEmployee.ec_number, EfficiencyEmployee.id)
    result = await session.execute(stmt)
    return {ec: emp_id for ec, emp_id in result.all()}


async def _load_machines_map(session: AsyncSession) -> Dict[str, int]:
    """Load all machines into a map: machine_code -> id"""
    stmt = select(Machine.machine_code, Machine.id)
    result = await session.execute(stmt)
    return {code: machine_id for code, machine_id in result.all()}


async def _load_work_orders_map(session: AsyncSession) -> Dict[str, int]:
    """Load all work orders into a map: wo_number -> id"""
    stmt = select(WorkOrder.wo_number, WorkOrder.id)
    result = await session.execute(stmt)
    return {wo: wo_id for wo, wo_id in result.all()}


async def _load_activity_codes_map(session: AsyncSession) -> Dict[str, int]:
    """Load all activity codes into a map: code -> id"""
    stmt = select(ActivityCode.code, ActivityCode.id)
    result = await session.execute(stmt)
    return {code: act_id for code, act_id in result.all()}


async def _validate_and_map_row(
    row_data: dict,
    row_num: int,
    employees_map: Dict[str, int],
    machines_map: Dict[str, int],
    work_orders_map: Dict[str, int],
    activity_codes_map: Dict[str, int],
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Validate and map a single row to jobcard data.
    
    Returns:
        (jobcard_data_dict, error_message)
        If error_message is not None, validation failed.
    """
    # Extract and clean data
    ec_number = str(row_data.get('ec_number', '')).strip()
    machine_code = str(row_data.get('machine_code', '')).strip()
    wo_number = str(row_data.get('wo_number', '')).strip()
    activity_code_str = str(row_data.get('activity_code', '')).strip()
    activity_desc = str(row_data.get('activity_desc', '')).strip()
    status_str = str(row_data.get('status', '')).strip().upper()
    
    # Parse entry_date
    try:
        entry_date_value = row_data.get('entry_date')
        if pd.isna(entry_date_value):
            return None, "Missing entry_date"
        
        # Handle different date formats
        if isinstance(entry_date_value, str):
            # Try YYYY-MM-DD
            try:
                entry_date = datetime.strptime(entry_date_value, '%Y-%m-%d').date()
            except ValueError:
                # Try DD/MM/YYYY
                try:
                    entry_date = datetime.strptime(entry_date_value, '%d/%m/%Y').date()
                except ValueError:
                    return None, f"Invalid date format: {entry_date_value}. Use YYYY-MM-DD or DD/MM/YYYY"
        elif isinstance(entry_date_value, pd.Timestamp):
            entry_date = entry_date_value.date()
        elif isinstance(entry_date_value, date):
            entry_date = entry_date_value
        else:
            return None, f"Unsupported date type: {type(entry_date_value)}"
    except Exception as e:
        return None, f"Date parsing error: {str(e)}"
    
    # Parse numeric fields
    try:
        qty = float(row_data.get('qty', 0))
        actual_hours = float(row_data.get('actual_hours', 0))
    except (ValueError, TypeError) as e:
        return None, f"Invalid numeric value: {str(e)}"
    
    # Validate employee
    if not ec_number or ec_number not in employees_map:
        return None, f"Employee not found: {ec_number}"
    
    # Validate machine
    if not machine_code or machine_code not in machines_map:
        return None, f"Machine not found: {machine_code}"
    
    # Validate work order
    if not wo_number or wo_number not in work_orders_map:
        return None, f"Work order not found: {wo_number}"
    
    # Validate activity code (optional - can be None/empty for AWC cases)
    activity_code_id = None
    if activity_code_str and activity_code_str not in ('', 'nan', 'None', 'N/A'):
        if activity_code_str in activity_codes_map:
            activity_code_id = activity_codes_map[activity_code_str]
        else:
            return None, f"Activity code not found: {activity_code_str}"
    
    # Validate status
    if status_str not in ('C', 'IC'):
        return None, f"Invalid status: {status_str}. Must be C or IC"
    
    # Build jobcard data
    jobcard_data = {
        'employee_id': employees_map[ec_number],
        'machine_id': machines_map[machine_code],
        'work_order_id': work_orders_map[wo_number],
        'activity_code_id': activity_code_id,
        'activity_desc': activity_desc or 'Imported work',
        'qty': qty,
        'actual_hours': actual_hours,
        'status': JobCardStatusEnum(status_str),
        'entry_date': entry_date,
    }
    
    return jobcard_data, None

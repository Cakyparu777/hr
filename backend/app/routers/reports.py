from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime
import pandas as pd
import io
from app.core.dependencies import get_current_accountant_user
from app.db.dynamodb import get_all_timelogs, get_all_users

router = APIRouter()

@router.get("/summary")
async def get_summary_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    current_user = Depends(get_current_accountant_user)
):
    """Get summary statistics for time logs."""
    logs = await get_all_timelogs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    
    if not logs:
        return {
            "total_hours": 0,
            "total_overtime_hours": 0,
            "total_entries": 0,
            "average_hours_per_day": 0,
            "overtime_entries": 0
        }
    
    total_hours = sum(float(log.get("total_hours", 0)) for log in logs)
    overtime_logs = [log for log in logs if log.get("is_overtime", False)]
    total_overtime_hours = sum(float(log.get("total_hours", 0)) for log in overtime_logs)
    
    # Calculate unique days
    unique_days = len(set(log.get("start_time", "")[:10] for log in logs))
    avg_hours = total_hours / unique_days if unique_days > 0 else 0
    
    return {
        "total_hours": round(total_hours, 2),
        "total_overtime_hours": round(total_overtime_hours, 2),
        "total_entries": len(logs),
        "average_hours_per_day": round(avg_hours, 2),
        "overtime_entries": len(overtime_logs)
    }

@router.get("/export/csv")
async def export_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    current_user = Depends(get_current_accountant_user)
):
    """Export time logs to CSV."""
    logs = await get_all_timelogs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    users = await get_all_users()
    user_map = {user["user_id"]: user["name"] for user in users}
    
    # Prepare data
    data = []
    for log in logs:
        data.append({
            "Date": log.get("start_time", "")[:10],
            "Employee": user_map.get(log.get("user_id", ""), "Unknown"),
            "Start Time": log.get("start_time", ""),
            "End Time": log.get("end_time", ""),
            "Break Duration (hours)": log.get("break_duration", 0),
            "Total Hours": log.get("total_hours", 0),
            "Overtime": "Yes" if log.get("is_overtime", False) else "No"
        })
    
    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=timelogs_export.csv"}
    )

@router.get("/export/excel")
async def export_excel(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    current_user = Depends(get_current_accountant_user)
):
    """Export time logs to Excel."""
    logs = await get_all_timelogs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    users = await get_all_users()
    user_map = {user["user_id"]: user["name"] for user in users}
    
    # Prepare data
    data = []
    for log in logs:
        data.append({
            "Date": log.get("start_time", "")[:10],
            "Employee": user_map.get(log.get("user_id", ""), "Unknown"),
            "Start Time": log.get("start_time", ""),
            "End Time": log.get("end_time", ""),
            "Break Duration (hours)": log.get("break_duration", 0),
            "Total Hours": log.get("total_hours", 0),
            "Overtime": "Yes" if log.get("is_overtime", False) else "No"
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Time Logs')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=timelogs_export.xlsx"}
    )


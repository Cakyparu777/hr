from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.holiday import HolidayCreate, HolidayResponse
from app.core.dependencies import get_current_admin_user
from app.db.dynamodb import create_holiday, get_all_holidays, delete_holiday

router = APIRouter()

@router.post("/", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
async def create_holiday_endpoint(holiday_data: HolidayCreate, current_user = Depends(get_current_admin_user)):
    """Create a new holiday."""
    holiday = await create_holiday(holiday_data.dict())
    return holiday

@router.get("/", response_model=List[HolidayResponse])
async def get_all_holidays_endpoint():
    """Get all holidays."""
    holidays = await get_all_holidays()
    return holidays

@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday_endpoint(holiday_id: str, current_user = Depends(get_current_admin_user)):
    """Delete a holiday."""
    success = await delete_holiday(holiday_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holiday not found"
        )
    return None

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import date, datetime
import httpx
from app.models.holiday import HolidayCreate, HolidayResponse
from app.core.dependencies import get_current_admin_user
from app.db.dynamodb import create_holiday, get_all_holidays, delete_holiday, create_holiday_if_not_exists
from app.core.logging_config import get_logger

logger = get_logger(__name__)

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

@router.post("/sync-jp-holidays", status_code=status.HTTP_200_OK)
async def sync_jp_holidays_endpoint(current_user = Depends(get_current_admin_user)):
    """
    Sync Japanese public holidays from the holidays-jp API.
    Fetches holidays and adds them to the database if they don't already exist.
    """
    try:
        # Fetch holidays from the Japanese Holidays API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://holidays-jp.github.io/api/v1/date.json")
            response.raise_for_status()
            holidays_data = response.json()
        
        # Load all existing holidays once to avoid repeated scans
        existing_holidays = await get_all_holidays()
        existing_dates = set()
        for holiday in existing_holidays:
            # Parse the date from the holiday item
            holiday_date_str = holiday.get("date")
            if holiday_date_str:
                try:
                    if isinstance(holiday_date_str, str):
                        existing_date = datetime.fromisoformat(holiday_date_str).date()
                    else:
                        existing_date = holiday_date_str
                    existing_dates.add(existing_date.isoformat())
                except Exception:
                    continue
        
        # Process the holidays (API returns { "YYYY-MM-DD": "Holiday Name", ... })
        synced_count = 0
        skipped_count = 0
        errors = []
        
        for date_str, holiday_name in holidays_data.items():
            try:
                # Parse the date string (YYYY-MM-DD format)
                holiday_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # Check if holiday already exists (in-memory check)
                if date_str in existing_dates:
                    skipped_count += 1
                    continue
                
                # Create holiday
                holiday_data = {
                    "name": holiday_name,
                    "date": holiday_date
                }
                await create_holiday(holiday_data)
                synced_count += 1
                # Add to existing dates to avoid duplicates in the same batch
                existing_dates.add(date_str)
                    
            except Exception as e:
                logger.error(f"Error processing holiday {date_str}: {str(e)}")
                errors.append(f"{date_str}: {str(e)}")
                continue
        
        return {
            "message": "Holidays synced successfully",
            "synced": synced_count,
            "skipped": skipped_count,
            "errors": errors if errors else None
        }
        
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch holidays from API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch holidays from API: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error syncing holidays: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing holidays: {str(e)}"
        )

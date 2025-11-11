#!/usr/bin/env python3
"""
Script to recalculate overtime for all existing time logs based on daily totals.
This is a one-time migration script to update existing logs with the new overtime calculation logic.
"""
import asyncio
import sys
from datetime import datetime, date
from app.db.dynamodb import get_all_timelogs, get_all_users
from app.services.timelog_service import calculate_daily_overtime

async def recalculate_all_overtime():
    """Recalculate overtime for all time logs."""
    print("Starting overtime recalculation for all logs...")
    
    # Get all users
    users, _ = await get_all_users()
    print(f"Found {len(users)} users")
    
    # Get all timelogs (handle pagination)
    all_logs = []
    last_key = None
    page_count = 0
    
    while True:
        logs, last_key = await get_all_timelogs(page_size=100, last_evaluated_key=last_key)
        all_logs.extend(logs)
        page_count += 1
        print(f"Fetched page {page_count}: {len(logs)} logs (total: {len(all_logs)})")
        if not last_key:
            break
    
    print(f"Found {len(all_logs)} total time logs")
    
    if not all_logs:
        print("No time logs found. Nothing to recalculate.")
        return
    
    # Group logs by user and date
    user_date_logs = {}
    for log in all_logs:
        user_id = log.get("user_id")
        start_time = log.get("start_time")
        
        if not user_id or not start_time:
            continue
        
        # Parse start_time (could be datetime object or string)
        if isinstance(start_time, datetime):
            log_date = start_time.date()
        elif isinstance(start_time, str):
            try:
                # Handle timezone-aware and naive strings
                if start_time.endswith('Z'):
                    start_time = start_time.replace('Z', '+00:00')
                log_date = datetime.fromisoformat(start_time).date()
            except Exception as e:
                print(f"Warning: Could not parse start_time {start_time}: {e}")
                continue
        else:
            continue
        
        # Create date key
        user_date_key = (user_id, log_date)
        
        if user_date_key not in user_date_logs:
            user_date_logs[user_date_key] = []
        user_date_logs[user_date_key].append(log)
    
    print(f"Found {len(user_date_logs)} unique user-date combinations")
    
    # Recalculate overtime for each user-date combination
    processed = 0
    errors = 0
    for (user_id, log_date), date_logs in user_date_logs.items():
        # Create datetime for the date (use UTC midnight for consistency)
        date_dt = datetime.combine(log_date, datetime.min.time())
        
        try:
            await calculate_daily_overtime(user_id, date_dt)
            processed += 1
            if processed % 10 == 0:
                print(f"Processed {processed}/{len(user_date_logs)} user-date combinations...")
        except Exception as e:
            errors += 1
            print(f"Error processing user {user_id} date {log_date}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n✓ Completed!")
    print(f"  Processed: {processed} user-date combinations")
    print(f"  Errors: {errors}")
    print(f"  Total logs affected: {len(all_logs)}")

if __name__ == "__main__":
    asyncio.run(recalculate_all_overtime())

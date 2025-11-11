#!/usr/bin/env python3
"""
Debug script to check overtime calculations for logs.
"""
import asyncio
from datetime import datetime
from app.db.dynamodb import get_all_timelogs, get_all_users
from app.core.config import settings

async def debug_overtime():
    """Debug overtime calculations."""
    print("=== Overtime Debug Information ===\n")
    
    # Get all users
    users, _ = await get_all_users()
    user_map = {user["user_id"]: user["name"] for user in users}
    
    # Get all timelogs
    all_logs = []
    last_key = None
    
    while True:
        logs, last_key = await get_all_timelogs(page_size=100, last_evaluated_key=last_key)
        all_logs.extend(logs)
        if not last_key:
            break
    
    print(f"Total logs: {len(all_logs)}\n")
    
    # Group by user and date
    user_date_logs = {}
    for log in all_logs:
        user_id = log.get("user_id")
        start_time = log.get("start_time")
        
        if not user_id or not start_time:
            continue
        
        # Parse start_time
        if isinstance(start_time, datetime):
            log_date = start_time.date()
        elif isinstance(start_time, str):
            try:
                if start_time.endswith('Z'):
                    start_time = start_time.replace('Z', '+00:00')
                log_date = datetime.fromisoformat(start_time).date()
            except:
                continue
        else:
            continue
        
        user_date_key = (user_id, log_date)
        if user_date_key not in user_date_logs:
            user_date_logs[user_date_key] = []
        user_date_logs[user_date_key].append(log)
    
    # Calculate and display overtime per user-date
    total_overtime = 0.0
    for (user_id, log_date), date_logs in sorted(user_date_logs.items()):
        user_name = user_map.get(user_id, "Unknown")
        total_entries = len(date_logs)
        total_hours = sum(float(log.get("total_hours", 0)) for log in date_logs)
        expected_hours = total_entries * settings.OVERTIME_THRESHOLD_HOURS
        daily_overtime = max(0, total_hours - expected_hours)
        total_overtime += daily_overtime
        
        # Sum up overtime_hours from logs
        sum_overtime_hours = sum(float(log.get("overtime_hours", 0)) for log in date_logs)
        
        print(f"User: {user_name}, Date: {log_date}")
        print(f"  Entries: {total_entries}")
        print(f"  Total Hours: {total_hours}")
        print(f"  Expected Hours: {expected_hours} ({total_entries} × {settings.OVERTIME_THRESHOLD_HOURS})")
        print(f"  Calculated Overtime: {daily_overtime}")
        print(f"  Sum of overtime_hours field: {sum_overtime_hours}")
        print(f"  Logs with is_overtime=True: {sum(1 for log in date_logs if log.get('is_overtime', False))}")
        
        # Show individual log details
        for log in date_logs:
            print(f"    - Log {log.get('log_id', '')[:8]}: {log.get('total_hours', 0)}h, "
                  f"overtime_hours={log.get('overtime_hours', 0)}, "
                  f"is_overtime={log.get('is_overtime', False)}")
        print()
    
    print(f"\n=== Summary ===")
    print(f"Total overtime across all days: {total_overtime}")
    print(f"Total logs: {len(all_logs)}")
    print(f"Total hours: {sum(float(log.get('total_hours', 0)) for log in all_logs)}")
    print(f"Sum of overtime_hours fields: {sum(float(log.get('overtime_hours', 0)) for log in all_logs)}")

if __name__ == "__main__":
    asyncio.run(debug_overtime())


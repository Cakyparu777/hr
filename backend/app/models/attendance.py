from pydantic import BaseModel
from typing import Optional
from enum import Enum

class AttendanceType(str, Enum):
    """Attendance types in Japanese (with English translations)"""
    WORK = "work"  # 出動
    STATUTORY_HOLIDAY = "statutory_holiday"  # 法定休日
    PAID_LEAVE = "paid_leave"  # 有給休暇
    SPECIAL_LEAVE = "special_leave"  # 特別休暇

class WorkLocation(str, Enum):
    """Work location types (when attendance type is WORK)"""
    OFFICE = "office"  # 自社
    CLIENT_SITE = "client_site"  # 客先
    REMOTE = "remote"  # 在宅

# Helper function to get display names
def get_attendance_type_display(attendance_type: AttendanceType) -> str:
    """Get Japanese display name for attendance type"""
    names = {
        AttendanceType.WORK: "出動",
        AttendanceType.STATUTORY_HOLIDAY: "法定休日",
        AttendanceType.PAID_LEAVE: "有給休暇",
        AttendanceType.SPECIAL_LEAVE: "特別休暇",
    }
    return names.get(attendance_type, attendance_type.value)

def get_work_location_display(location: WorkLocation) -> str:
    """Get Japanese display name for work location"""
    names = {
        WorkLocation.OFFICE: "自社",
        WorkLocation.CLIENT_SITE: "客先",
        WorkLocation.REMOTE: "在宅",
    }
    return names.get(location, location.value)

def get_leave_type_display(leave_type: str) -> str:
    """Get Japanese display name for leave type"""
    names = {
        "statutory_holiday": "法定休日",
        "non_statutory_holiday": "法定外休日",
        "paid_leave": "有給休暇",
        "special_leave": "特別休暇",
    }
    return names.get(leave_type, leave_type)


from pydantic import BaseModel, Field
from datetime import date

class HolidayBase(BaseModel):
    name: str
    date: date

class HolidayCreate(HolidayBase):
    pass

class HolidayResponse(HolidayBase):
    holiday_id: str = Field(..., alias="id")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

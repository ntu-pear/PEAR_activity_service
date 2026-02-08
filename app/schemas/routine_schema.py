from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime, date, time, timezone

class RoutineBase(BaseModel):
    name: str = Field(..., max_length=255, description="Name of the routine")
    activity_id: int = Field(..., description="Activity assigned to patient")
    patient_id: int = Field(..., description="ID of the patient")
    day_of_week: int = Field(..., ge=1, le=127, description="Bitmask for days of week (Monday=1, Tuesday=2, Wednesday=4, Thursday=8, Friday=16, Saturday=32, Sunday=64)")
    start_time: time = Field(..., description="Start time of the routine")
    end_time: time = Field(..., description="End time of the routine")
    start_date: date = Field(..., description="Date when routine starts")
    end_date: date = Field(..., description="Date when routine ends")

class ValidatedRoutine(RoutineBase):
    @model_validator(mode="after")
    def validate_routine(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        
        today = date.today()
        if self.start_date < today:
            raise ValueError("start_date cannot be in the past")
        
        return self

class RoutineCreate(ValidatedRoutine):
    pass

class RoutineUpdate(ValidatedRoutine):
    id: int = Field(..., description="ID of the routine to update")

class RoutineResponse(RoutineBase):
    id: int = Field(..., description="Record ID")
    is_deleted: bool = Field(..., description="Soft-delete flag")
    created_date: datetime = Field(..., description="When record was created")
    modified_date: Optional[datetime] = Field(..., description="When record was last changed")
    created_by_id: str = Field(..., description="Who created it")
    modified_by_id: Optional[str] = Field(..., description="Who last modified it")

    class Config:
        from_attributes = True

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime, date, time, timezone

class RoutineBase(BaseModel):
    name: str = Field(..., max_length=255, description="Name of the routine")
    activity_id: int = Field(..., description="Activity assigned to patient")
    patient_id: int = Field(..., description="ID of the patient")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
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
        
        if self.day_of_week < 0 or self.day_of_week > 6:
            raise ValueError("day_of_week must be between 0 (Monday) and 6 (Sunday)")
        
        return self

class RoutineCreate(ValidatedRoutine):
    created_by_id: str = Field(..., description="User who creates this record")

class RoutineUpdate(ValidatedRoutine):
    id: int = Field(..., description="ID of the routine to update")
    is_deleted: bool = Field(False, description="Soft-delete flag")
    modified_by_id: str = Field(..., description="User who last modified this record")
    modified_date: Optional[datetime] = Field(None, description="Timestamp of last modification")

class RoutineResponse(RoutineBase):
    id: int = Field(..., description="Record ID")
    is_deleted: bool = Field(..., description="Soft-delete flag")
    created_date: datetime = Field(..., description="When record was created")
    modified_date: Optional[datetime] = Field(..., description="When record was last changed")
    created_by_id: str = Field(..., description="Who created it")
    modified_by_id: Optional[str] = Field(..., description="Who last modified it")

    class Config:
        from_attributes = True

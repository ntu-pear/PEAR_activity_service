from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime, date

class RoutineExclusionBase(BaseModel):
    routine_id: int = Field(..., description="ID of the routine to exclude")
    start_date: date = Field(..., description="Date when exclusion starts")
    end_date: date = Field(..., description="Date when exclusion ends")
    remarks: Optional[str] = Field(None, description="Reason for exclusion")

class ValidatedRoutineExclusion(RoutineExclusionBase):
    @model_validator(mode="after")
    def validate_routine_exclusion(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self

class RoutineExclusionCreate(ValidatedRoutineExclusion):
    pass

class RoutineExclusionUpdate(ValidatedRoutineExclusion):
    id: int = Field(..., description="ID of the routine exclusion to update")

class RoutineExclusionResponse(RoutineExclusionBase):
    id: int = Field(..., description="Record ID")
    is_deleted: bool = Field(..., description="Soft-delete flag")
    created_date: datetime = Field(..., description="When record was created")
    modified_date: Optional[datetime] = Field(..., description="When record was last changed")
    created_by_id: str = Field(..., description="Who created it")
    modified_by_id: Optional[str] = Field(..., description="Who last modified it")

    class Config:
        from_attributes = True

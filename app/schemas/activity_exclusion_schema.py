from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import date, datetime

class ActivityExclusionBase(BaseModel):
    activity_id: int = Field(..., description="ID of the Activity to exclude")
    patient_id:  int = Field(..., description="ID of the Patient")
    exclusion_remarks: Optional[str] = Field(None, description="Why this exclusion")
    start_date: date = Field(..., description="Date to start excluding")
    end_date:   Optional[date] = Field(None, description="Date to end exclusion")

class ActivityExclusionCreate(ActivityExclusionBase):
    pass

class ActivityExclusionUpdate(ActivityExclusionBase):
    id: int = Field(..., description="Record ID")
    is_deleted: Optional[bool] = Field(None, description="Soft-delete flag")
    modified_by_id: str = Field(..., description="User performing update")

class ActivityExclusionResponse(ActivityExclusionBase):
    id: int
    is_deleted: bool
    created_date: datetime
    modified_date: datetime
    created_by_id: Optional[str]
    modified_by_id: Optional[str]

    class Config:
        from_attributes = True
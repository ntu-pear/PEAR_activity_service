from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import datetime, timedelta, timezone

class AdhocBase(BaseModel):
    old_centre_activity_id: int = Field(..., description="CentreActivity being replaced")
    new_centre_activity_id: int = Field(..., description="CentreActivity replacement")
    patient_id: int = Field(..., description="ID of the patient to apply this ad-hoc")
    status: Literal["PENDING", "APPROVED", "REJECTED"] = Field(..., description="Adhoc request status")
    start_date: datetime = Field(..., description="When the adhoc starts")
    end_date: datetime = Field(..., description="When the adhoc ends")

class ValidatedAdhoc(AdhocBase):
    @model_validator(mode="after")
    def validate_adhoc(self):
        if self.old_centre_activity_id == self.new_centre_activity_id:
            raise ValueError("Old centre activity ID and new centre activity ID must be different.")
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date.")
        now = datetime.now(timezone.utc) 
        if self.start_date < now:
            raise ValueError("Start date cannot be in the past.")
        days_to_sunday = 6 - now.weekday()
        end_of_week = (
            now
            .replace(hour=23, minute=59, second=59, microsecond=0)
            + timedelta(days=days_to_sunday)
        )
        if self.end_date > end_of_week:
            raise ValueError("end_date cannot go beyond the end of the current week.")
        return self

class AdhocCreate(ValidatedAdhoc):
    created_by_id: str = Field(..., description="User who creates this record")

class AdhocUpdate(ValidatedAdhoc):
    id: int = Field(..., description="ID of the record to update")
    is_deleted: bool = Field(False, description="Soft-delete flag")
    modified_by_id: str = Field(..., description="User who last modified this record")
    modified_date: Optional[datetime] = Field(None, description="Timestamp of last modification")

class AdhocResponse(AdhocBase):
    id: int = Field(..., description="Record ID")
    is_deleted: bool = Field(..., description="Soft-delete flag")
    created_date: datetime = Field(..., description="When record was created")
    modified_date: Optional[datetime] = Field(..., description="When record was last changed")
    created_by_id: str = Field(..., description="Who created it")
    modified_by_id: Optional[str] = Field(..., description="Who last modified it")

    class Config:
        from_attributes = True
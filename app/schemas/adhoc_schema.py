from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime, timezone

class AdhocBase(BaseModel):
    old_centre_activity_id: int = Field(..., description="CentreActivity being replaced")
    new_centre_activity_id: int = Field(..., description="CentreActivity replacement")
    status: str = Field(..., description="Adhoc request status (e.g. PENDING, APPROVED, REJECTED)")
    start_time: datetime = Field(..., description="When the adhoc starts")
    end_time: datetime = Field(..., description="When the adhoc ends")

    @model_validator(mode='after')
    def validate_input(self):
        if self.old_centre_activity_id == self.new_centre_activity_id:
            raise ValueError("Old centre activity ID and new centre activity ID must be different.")
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time.")
        now = datetime.now(timezone.utc)
        if self.start_time < now:
            raise ValueError("Start time cannot be in the past.")
        return self

class AdhocCreate(AdhocBase):
    created_by_id: str = Field(..., description="User who creates this record")

class AdhocUpdate(AdhocBase):
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
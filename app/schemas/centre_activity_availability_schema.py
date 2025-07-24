from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime, timedelta, timezone, date

class CentreActivityAvailabilityBase(BaseModel):
    centre_activity_id: int = Field(..., description="Reference to Centre Activity")

    start_time: date = Field(..., description="Specific Date and Start time of the Centre Activity Availability")
    end_time: date = Field(None, description="Specific Date and End time of the Centre Activity Availability. Must be same date as start_date.")

    @model_validator(mode='after')
    def validate_input(self):
        start_time = self.start_time
        end_time = self.end_time

        #Availability's start and end time will be checked in crud functions
        if start_time and start_time < datetime.now(timezone.utc).date():
            raise ValueError("The start date cannot be in the past.")
        if end_time and end_time < self.start_time:
            raise ValueError("The end date cannot be before the start date.")
        if end_time and end_time > (datetime.now(timezone.utc) + timedelta(days=365)).date():
            raise ValueError("End date cannot be more than 1 year in the future.")
        if date(self.start_time) != date(self.end_time):
            raise ValueError("Both the start date and end date are not the same.")
        return self

class CentreActivityAvailabilityCreate(CentreActivityAvailabilityBase):
    created_by_id: str = Field(..., description="ID of the user who created this Centre Activity Availability")

class CentreActivityAvailabilityUpdate(CentreActivityAvailabilityBase):
    id: int = Field(..., description="ID of the Centre Activity Availability to update")
    is_deleted: bool = Field(False, description="Is the Centre Activity Availability deleted")
    modified_by_id: str = Field(..., description="ID of the user who last modified this Centre Activity Availability")
    modified_date: datetime = Field(None, description="Last modification timestamp")

class CentreActivityAvailabilityResponse(CentreActivityAvailabilityBase):
    id: int = Field(..., description="ID of the Centre Activity Availability")
    is_deleted: bool = Field(..., description="Is the Centre Activity Availability deleted")

    created_date: datetime = Field(..., description="Creation date of the Centre Activity Availability")
    modified_date: Optional[datetime] = Field(..., description="Last modification date of the Centre Activity Availability")
    created_by_id: str = Field(..., description="ID of the user who created this Centre Activity Availability")
    modified_by_id: Optional[str] = Field(..., description="ID of the user who last modified this Centre Activity Availability")

    class Config:
        from_attributes = True
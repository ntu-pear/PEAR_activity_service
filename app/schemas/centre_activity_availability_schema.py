from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime, timedelta, timezone

class CentreActivityAvailabilityBase(BaseModel):
    centre_activity_id: int = Field(..., description="Reference to Centre Activity")
    start_time: datetime = Field(..., description="Specific Date and Start time of the Centre Activity Availability. If recurring every day, it will hold the specific start time of the Centre Activity Availability.")
    end_time: datetime = Field(..., description="Specific Date and End time of the Centre Activity Availability. Must be same date as start_date. If recurring every day, it will hold the specific end time of the Centre Activity Availability.")

class ValidatedCentreActivityAvailability(CentreActivityAvailabilityBase):
    @model_validator(mode='after')
    def validate_input(self):
        #Clean datetime variables
        self.start_time = self.start_time.replace(tzinfo=timezone.utc, second=0, microsecond=0)
        self.end_time = self.end_time.replace(tzinfo=timezone.utc, second=0, microsecond=0)
        
        start_time = self.start_time
        end_time = self.end_time

        if start_time and start_time.date() < datetime.now(timezone.utc).date():
            raise ValueError("The start date cannot be in the past.")
        if end_time and end_time.date() < start_time.date():
            raise ValueError("The end date cannot be before the start date.")
        if end_time and end_time.date() > (datetime.now(timezone.utc) + timedelta(days=365)).date():
            raise ValueError("End date cannot be more than 1 year in the future.")
        if start_time.date() != end_time.date():
            raise ValueError("Both the start time date and end time date are not the same.")
        if start_time.time() > end_time.time():
            raise ValueError("Start time cannot be after end time.")
        if end_time.time() < start_time.time():
            raise ValueError("End time cannot be before start time.")
        if start_time.time() == end_time.time():
            raise ValueError("Both the start time and end time are the same.")
        return self
    
class CentreActivityAvailabilityCreate(ValidatedCentreActivityAvailability):
    created_by_id: str = Field(..., description="ID of the user who created this Centre Activity Availability")

class CentreActivityAvailabilityUpdate(ValidatedCentreActivityAvailability):
    id: int = Field(..., description="ID of the Centre Activity Availability to update")
    is_deleted: bool = Field(..., description="Is the Centre Activity Availability deleted")
    is_fixed: bool =Field(..., description="Is the Centre Activity Availability only allowed to occur at the indicated start time and end time")
    modified_by_id: str = Field(..., description="ID of the user who last modified this Centre Activity Availability")
    modified_date: datetime = Field(None, description="Last modification timestamp")

class CentreActivityAvailabilityResponse(CentreActivityAvailabilityBase):
    id: int = Field(..., description="ID of the Centre Activity Availability")
    is_deleted: bool = Field(..., description="Is the Centre Activity Availability deleted")
    is_fixed: bool =Field(..., description="Is the Centre Activity Availability only allowed to occur at the indicated start time and end time")
    created_date: datetime = Field(..., description="Creation date of the Centre Activity Availability")
    modified_date: Optional[datetime] = Field(..., description="Last modification date of the Centre Activity Availability")
    created_by_id: str = Field(..., description="ID of the user who created this Centre Activity Availability")
    modified_by_id: Optional[str] = Field(..., description="ID of the user who last modified this Centre Activity Availability")

    class Config:
        from_attributes = True
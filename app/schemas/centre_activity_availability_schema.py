from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime, timedelta, timezone, time

class CentreActivityAvailabilityBase(BaseModel):
    centre_activity_id: int = Field(..., description="Reference to Centre Activity")
    start_time: time = Field(..., description="Specific Date and Start time of the Centre Activity Availability. If recurring every day, it will hold the specific start time of the Centre Activity Availability.")
    end_time: time = Field(..., description="Specific Date and End time of the Centre Activity Availability. Must be same date as start_date. If recurring every day, it will hold the specific end time of the Centre Activity Availability.")
    days_of_week: int = Field(..., description="Bitmask representing the days of the week the activity recurs on. 0 means non-recurring. 1 means Monday, 2 means Tuesday, 4 means Wednesday, and so on. For example, a value of 3 (1+2) means the activity recurs on Monday and Tuesday.")

class ValidatedCentreActivityAvailability(CentreActivityAvailabilityBase):
    @model_validator(mode='after')
    def validate_input(self):
        #Clean datetime variables
        self.start_time = self.start_time.replace(tzinfo=None, second=0, microsecond=0)
        self.end_time = self.end_time.replace(tzinfo=None, second=0, microsecond=0)
        
        start_time = self.start_time
        end_time = self.end_time

        if start_time > end_time:
            raise ValueError("Start time cannot be after end time.")
        if start_time == end_time:
            raise ValueError("Both the start time and end time are the same.")
        return self
    
class CentreActivityAvailabilityCreate(ValidatedCentreActivityAvailability):
    created_by_id: str = Field(..., description="ID of the user who created this Centre Activity Availability")

class CentreActivityAvailabilityUpdate(ValidatedCentreActivityAvailability):
    id: int = Field(..., description="ID of the Centre Activity Availability to update")
    is_deleted: bool = Field(..., description="Is the Centre Activity Availability deleted")
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
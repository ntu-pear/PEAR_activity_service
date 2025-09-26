from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime, timedelta, timezone, date

class CentreActivityBase(BaseModel):
    activity_id: int = Field(..., description="Reference to Activity")
    is_compulsory: bool = Field(..., description="Is compulsory")
    is_fixed: bool = Field(..., description="Is fixed duration")
    is_group: bool = Field(..., description="Is group activity")

    start_date: date = Field(..., description="Start date of the activity")
    end_date: date = Field(..., description="End date of the activity. If indefinite, use a far in the future date (i.e Year 2999).")

    min_duration: int = Field(60, description="Minimum duration in minutes")
    max_duration: int = Field(60, description="Maximum duration in minutes")
    min_people_req: int = Field(1, description="Minimum number of people required", ge=1)
    fixed_time_slots: Optional[str] = Field(None, description="Fixed time slots if any")


class ValidatedCentreActivity(CentreActivityBase):
    """Mixin class that adds validation to CentreActivityBase - used by Create and Update classes"""
    
    @model_validator(mode='after')
    def validate_input(self):
        is_fixed = self.is_fixed
        is_group = self.is_group
        start_date = self.start_date
        end_date = self.end_date
        min_duration = self.min_duration
        max_duration = self.max_duration
        min_people_req = self.min_people_req

        if is_group and (min_people_req is None or min_people_req < 2):
            raise ValueError("Group activities must have a minimum of 2 people required.")
        if not is_group and min_people_req != 1:
            raise ValueError("Individual activities must have a minimum of 1 person required.")
        if is_fixed and (min_duration is None or max_duration is None or min_duration != max_duration):
            raise ValueError("Fixed duration activities must have the same minimum and maximum duration.")
        if not is_fixed and (min_duration is None or max_duration is None or min_duration > max_duration):
            raise ValueError("Flexible activities, ensure minimum duration is less than or equal to maximum duration.")
        if is_fixed and (self.fixed_time_slots is None or self.fixed_time_slots.strip() == ''):
            raise ValueError("Fixed activities must have fixed time slots specified.")
        if min_duration is None or max_duration is None or min_duration != 60 or max_duration != 60:
            raise ValueError("Duration must be 60 minutes.")
        if start_date and start_date < datetime.now(timezone.utc).date():
            raise ValueError("Start date cannot be in the past.")
        if end_date and end_date < self.start_date:
            raise ValueError("End date cannot be before start date.")

    
        #if min_duration is None or min_duration not in (30, 60) or max_duration is None or max_duration not in (30, 60):
        #    raise ValueError("Duration must be either 30 or 60 minutes.")
        #if end_date and end_date > (datetime.now(timezone.utc) + timedelta(days=365)).date():
        #    raise ValueError("End date cannot be more than 1 year in the future.")
        return self

class CentreActivityCreate(ValidatedCentreActivity):
    created_by_id: str = Field(..., description="ID of the user who created this activity")

class CentreActivityUpdate(ValidatedCentreActivity):
    id: int = Field(..., description="ID of the Centre Activity to update")
    is_deleted: bool = Field(False, description="Is the Centre Activity deleted")
    modified_by_id: str = Field(..., description="ID of the user who last modified this activity")
    modified_date: datetime = Field(None, description="Last modification timestamp")
    

class CentreActivityResponse(CentreActivityBase):
    id: int = Field(..., description="ID of the Centre Activity")
    is_deleted: bool = Field(..., description="Is the Centre Activity deleted")

    created_date: datetime = Field(..., description="Creation date of the Centre Activity")
    modified_date: Optional[datetime] = Field(..., description="Last modification date of the Centre Activity")
    created_by_id: str = Field(..., description="ID of the user who created this activity")
    modified_by_id: Optional[str] = Field(..., description="ID of the user who last modified this activity")

    class Config:
        from_attributes = True
    


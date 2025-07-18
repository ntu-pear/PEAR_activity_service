from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime

class CentreActivityBase(BaseModel):
    activity_id: int = Field(..., description="Reference to Activity")
    is_compulsory: bool = Field(..., description="Is compulsory")
    is_fixed: bool = Field(..., description="Is fixed duration")
    is_group: bool = Field(..., description="Is group activity")

    min_duration: int = Field(..., description="Minimum duration in minutes")
    max_duration: int = Field(..., description="Maximum duration in minutes")
    min_people_req: int = Field(..., description="Minimum number of people required")
    #fixed_time_slots: Optional[List[str]] = Field(None, description="Fixed time slots if any")

    @model_validator(mode='after')
    def validate_input(self):
        is_fixed = self.is_fixed
        is_group = self.is_group
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
        if min_duration is None or min_duration not in (30, 60) or max_duration is None or max_duration not in (30, 60):
            raise ValueError("Duration must be either 30 or 60 minutes.")
        return self

class CentreActivityCreate(CentreActivityBase):
    created_by_id: str = Field(..., description="ID of the user who created this activity")

class CentreActivityUpdate(CentreActivityBase):
    modified_by_id: str = Field(..., description="ID of the user who last modified this activity")
    id: int = Field(..., description="ID of the Centre Activity to update")

class CentreActivityResponse(CentreActivityBase):
    id: int = Field(..., description="ID of the Centre Activity")
    is_deleted: bool = Field(..., description="Is the Centre Activity deleted")

    created_date: datetime = Field(..., description="Creation date of the Centre Activity")
    modified_date: datetime = Field(..., description="Last modification date of the Centre Activity")
    created_by_id: str = Field(..., description="ID of the user who created this activity")
    modified_by_id: str = Field(..., description="ID of the user who last modified this activity")

    class Config:
        from_attributes = True
    


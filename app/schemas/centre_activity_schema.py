from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional, List
from datetime import datetime, timedelta, timezone, date

from app.schemas.activity_rules import validate_activity_configuration

class CentreActivityBase(BaseModel):
    activity_id: int = Field(..., description="Reference to Activity")
    name: Optional[str] = Field(None, max_length=200, description="What this configuration is called, e.g. 'Breathing AM'. Falls back to the Activity title when unset.")
    care_centre_id: Optional[int] = Field(None, description="Reference to the Care Centre this configuration belongs to")
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
    """Mixin class that adds validation to CentreActivityBase - used by Create and Update classes.

    The rules themselves live in app/schemas/activity_rules.py, because an
    Activity Template carries the same fields and has to satisfy the same rules.
    Keep them there rather than inlining them here, or the two definitions drift.
    """

    @model_validator(mode='after')
    def validate_input(self):
        validate_activity_configuration(self)
        #if end_date and end_date > (datetime.now(timezone.utc) + timedelta(days=365)).date():
        #    raise ValueError("End date cannot be more than 1 year in the future.")
        return self

class CentreActivityCreate(ValidatedCentreActivity):
    created_by_id: str = Field(..., description="ID of the user who created this activity")

    @model_validator(mode='after')
    def validate_input(self):
        # Run the shared validations from the mixin first
        super().validate_input()

        start_date = self.start_date
        if start_date and start_date < datetime.now(timezone.utc).date():
            raise ValueError("Start date cannot be in the past.")

        return self

class CentreActivityUpdate(ValidatedCentreActivity):
    id: int = Field(..., description="ID of the Centre Activity to update")
    is_deleted: bool = Field(False, description="Is the Centre Activity deleted")
    modified_by_id: str = Field(..., description="ID of the user who last modified this activity")
    modified_date: datetime = Field(None, description="Last modification timestamp")

    @model_validator(mode='after')
    def validate_input(self):
        super().validate_input()
        return self

class CentreActivityResponse(CentreActivityBase):
    id: int = Field(..., description="ID of the Centre Activity")
    is_deleted: bool = Field(..., description="Is the Centre Activity deleted")

    created_date: datetime = Field(..., description="Creation date of the Centre Activity")
    modified_date: Optional[datetime] = Field(..., description="Last modification date of the Centre Activity")
    created_by_id: str = Field(..., description="ID of the user who created this activity")
    modified_by_id: Optional[str] = Field(..., description="ID of the user who last modified this activity")

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from datetime import date, datetime

from app.schemas.activity_rules import validate_activity_configuration


class ActivityTemplateBase(BaseModel):
    """The fields an activity needs before it can exist.

    This is the union of what ACTIVITY and CENTRE_ACTIVITY hold, minus
    activity_id, which does not exist until the template is applied.
    """
    name: str = Field(..., max_length=200, description="Names the template itself, e.g. 'Morning physiotherapy (standard)'. Distinct from the activity title it produces.")

    title: str = Field(..., max_length=200, description="Becomes the Activity title, e.g. 'Physiotherapy'")
    description: Optional[str] = Field(None, description="Becomes the Activity description")

    care_centre_id: Optional[int] = Field(None, description="Default Care Centre; the user can still change it when applying")
    is_compulsory: bool = Field(..., description="Is compulsory")
    is_fixed: bool = Field(..., description="Is fixed timing")
    is_group: bool = Field(..., description="Is group activity")

    start_date: date = Field(..., description="Default start date. Applying validates this is not in the past, so a template saved long ago needs it adjusted.")
    end_date: date = Field(..., description="Default end date. If indefinite, use a far in the future date (i.e Year 2999).")

    min_duration: int = Field(60, description="Minimum duration in minutes")
    max_duration: int = Field(60, description="Maximum duration in minutes")
    min_people_req: int = Field(1, description="Minimum number of people required", ge=1)
    fixed_time_slots: Optional[str] = Field(None, description="Fixed time slots if any")


class ValidatedActivityTemplate(ActivityTemplateBase):
    """Adds the shared activity rules - used by Create and Update.

    The rules come from app/schemas/activity_rules.py, the same ones the Centre
    Activity schema uses. A template that could not produce a valid centre
    activity is not worth storing.

    Note what is deliberately absent: the "start_date must not be in the past"
    rule that CentreActivityCreate applies. A template's start date is a stored
    default rather than a scheduled date, so it is allowed to go stale. The check
    applies when the template is applied, not when it is saved.
    """

    @model_validator(mode='after')
    def validate_input(self):
        validate_activity_configuration(self)
        return self


class ActivityTemplateCreate(ValidatedActivityTemplate):
    created_by_id: str = Field(..., description="ID of the user who created this template")


class ActivityTemplateUpdate(ValidatedActivityTemplate):
    id: int = Field(..., description="ID of the Activity Template to update")
    is_deleted: Optional[bool] = Field(False, description="Soft delete flag")
    modified_by_id: str = Field(..., description="ID of the user who last modified this template")


class ActivityTemplateResponse(ActivityTemplateBase):
    id: int = Field(..., description="ID of the Activity Template")
    is_deleted: bool = Field(..., description="Soft delete flag")
    created_date: datetime = Field(..., description="When the template was created")
    modified_date: Optional[datetime] = Field(None, description="When the template was last modified")
    created_by_id: str = Field(..., description="ID of the user who created this template")
    modified_by_id: Optional[str] = Field(None, description="ID of the user who last modified this template")

    model_config = ConfigDict(from_attributes=True)

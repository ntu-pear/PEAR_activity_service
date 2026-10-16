from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from datetime import date, datetime

from app.schemas.activity_rules import validate_activity_configuration


class ApplyTemplateRequest(BaseModel):
    """The values submitted when applying a template.

    The whole set, not a diff against the stored template. The client has already
    loaded the template, pre-filled the form and let the supervisor edit, so it
    holds the final values - sending them whole keeps the server from having to
    merge, and makes it plain that the stored template is read-only here.

    `name` is the one field with no counterpart on the template: it names the
    centre activity being produced, which is how Breathing AM and Breathing PM
    are told apart.
    """
    name: str = Field(..., max_length=200, description="Names the Centre Activity, e.g. 'Breathing AM'")

    title: str = Field(..., max_length=200, description="Activity title. Reused if an active activity already has it, created otherwise.")
    description: Optional[str] = Field(None, description="Activity description, used only when the activity is created")

    care_centre_id: Optional[int] = Field(None, description="Care Centre this configuration belongs to")
    is_compulsory: bool = Field(..., description="Is compulsory")
    is_fixed: bool = Field(..., description="Is fixed timing")
    is_group: bool = Field(..., description="Is group activity")

    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date. If indefinite, use a far in the future date (i.e Year 2999).")

    min_duration: int = Field(60, description="Minimum duration in minutes")
    max_duration: int = Field(60, description="Maximum duration in minutes")
    min_people_req: int = Field(1, description="Minimum number of people required", ge=1)
    fixed_time_slots: Optional[str] = Field(None, description="Fixed time slots if any")

    @model_validator(mode='after')
    def validate_input(self):
        validate_activity_configuration(self)
        # Unlike the stored template, this one is scheduled, so the same
        # not-in-the-past rule CentreActivityCreate applies holds here. A
        # template saved months ago carries a stale start_date and the
        # supervisor is expected to adjust it before submitting.
        if self.start_date < datetime.now().date():
            raise ValueError("Start date cannot be in the past.")
        return self


class ApplyTemplateResponse(BaseModel):
    """What applying a template produced."""
    activity_id: int = Field(..., description="The Activity, whether created or reused")
    activity_title: str = Field(..., description="Title of that Activity")
    activity_was_created: bool = Field(..., description="False when an existing activity with this title was reused")
    centre_activity_id: int = Field(..., description="The Centre Activity that was created")
    centre_activity_name: str = Field(..., description="Name of that Centre Activity")

    model_config = ConfigDict(from_attributes=True)

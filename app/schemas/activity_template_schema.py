from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime


class ActivityTemplateBase(BaseModel):
    """A blank activity form, which is allowed to be incompletely filled in.

    Only the template's own name and the activity title are required. Everything
    else is a default the supervisor can set now or leave until they apply the
    template - which is the point of a template being a form rather than a
    finished configuration.

    Deliberately NOT validated as a whole here. A template may hold a
    combination that would be rejected as a centre activity - a group with one
    person, or a fixed activity with no time slots - because the supervisor is
    expected to complete it when applying. ApplyTemplateRequest enforces the
    full rules at that point.
    """
    name: str = Field(..., max_length=200, description="Names the template itself, e.g. 'Morning physiotherapy (standard)'. Distinct from the activity title it produces.")

    title: str = Field(..., max_length=200, description="Becomes the Activity title, e.g. 'Physiotherapy'")
    description: Optional[str] = Field(None, description="Becomes the Activity description")

    care_centre_id: Optional[int] = Field(None, description="Default Care Centre; the user can still change it when applying")
    is_compulsory: bool = Field(False, description="Default for 'is compulsory'")
    is_fixed: bool = Field(False, description="Default for 'is fixed timing'")
    is_group: bool = Field(False, description="Default for 'is group activity'")

    start_date: date = Field(default_factory=date.today, description="Default start date. Applying rejects a date in the past, so a template saved long ago needs this adjusted at that point.")
    end_date: date = Field(default=date(2999, 1, 1), description="Default end date. If indefinite, leave the far-future default.")

    min_duration: int = Field(60, description="Default minimum duration in minutes")
    max_duration: int = Field(60, description="Default maximum duration in minutes")
    min_people_req: int = Field(1, description="Default minimum number of people. Must be at least 2 for a group activity, but that is only enforced on apply.", ge=1)
    fixed_time_slots: Optional[str] = Field(None, description="Default fixed time slots. Required on apply when the activity is fixed or compulsory.")


class ActivityTemplateCreate(ActivityTemplateBase):
    created_by_id: str = Field(..., description="ID of the user who created this template")


class ActivityTemplateUpdate(ActivityTemplateBase):
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

from pydantic import BaseModel, Field, model_validator, ValidationInfo
from typing import Optional, Dict, Literal, get_args
from datetime import datetime

class CentreActivityPreferenceBase(BaseModel):
    centre_activity_id: int = Field(..., description="ID of the Centre Activity")
    patient_id: int = Field(..., description="ID of the Patient")
    is_like: bool = Field(..., description="Indicates if the preference is a 'like' or 'dislike'")

class CentreActivityPreferenceCreate(CentreActivityPreferenceBase):
    created_by_id: str = Field(..., description="ID of the user who created this preference")

class CentreActivityPreferenceUpdate(CentreActivityPreferenceBase):
    centre_activity_preference_id: int = Field(..., description="ID of the Centre Activity Preference to update", alias="id")
    is_deleted: bool = Field(False, description="Is the Centre Activity Preference deleted")
    modified_by_id: str = Field(..., description="ID of the user who last modified this preference")
    modified_date: datetime = Field(None, description="Last modification timestamp")

class CentreActivityPreferenceResponse(CentreActivityPreferenceBase):
    centre_activity_preference_id: int = Field(..., description="ID of the Centre Activity Preference", alias='id')
    is_deleted: bool = Field(..., description="Is the Centre Activity Preference deleted")
    created_date: datetime = Field(..., description="Timestamp of creation")
    modified_date: Optional[datetime] = Field(None, description="Last modification timestamp")
    created_by_id: str = Field(..., description="ID of the user who created it")
    modified_by_id: Optional[str] = Field(None, description="ID of the user who last modified it")

    class Config:
        from_attributes = True
        populate_by_name = True  # Optional, but good for flexibility!
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CentreActivityRecommendationBase(BaseModel):
    centre_activity_id: int = Field(..., description="ID of the Centre Activity")
    patient_id: int = Field(..., description="ID of the Patient")
    doctor_id: int = Field(..., description="ID of the Doctor")
    doctor_remarks: Optional[str] = Field(None, description="Doctor's remarks for the recommendation")

class CentreActivityRecommendationCreate(CentreActivityRecommendationBase):
    created_by_id: str = Field(..., description="ID of the user who created this recommendation")

class CentreActivityRecommendationUpdate(CentreActivityRecommendationBase):
    centre_activity_recommendation_id: int = Field(..., description="ID of the Centre Activity Recommendation to update", alias="id")
    is_deleted: bool = Field(False, description="Is the Centre Activity Recommendation deleted")
    modified_by_id: str = Field(..., description="ID of the user who last modified this recommendation")
    modified_date: datetime = Field(None, description="Last modification timestamp")

class CentreActivityRecommendationResponse(CentreActivityRecommendationBase):
    centre_activity_recommendation_id: int = Field(..., description="ID of the Centre Activity Recommendation", alias='id')
    is_deleted: bool = Field(..., description="Is the Centre Activity Recommendation deleted")
    created_date: datetime = Field(..., description="Timestamp of creation")
    modified_date: Optional[datetime] = Field(None, description="Last modification timestamp")
    created_by_id: str = Field(..., description="ID of the user who created it")
    modified_by_id: Optional[str] = Field(None, description="ID of the user who last modified it")

    class Config:
        from_attributes = True
        populate_by_name = True

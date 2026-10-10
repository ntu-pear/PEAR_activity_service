from pydantic import BaseModel
from typing import List
from app.schemas.activity_schema import ActivityRead
from app.schemas.centre_activity_schema import CentreActivityResponse
from app.schemas.centre_activity_preference_schema import CentreActivityPreferenceResponse
from app.schemas.centre_activity_recommendation_schema import CentreActivityRecommendationResponse
from app.schemas.centre_activity_exclusion_schema import CentreActivityExclusionResponse
from app.schemas.ref_patient import RefPatient


class ActivityPreferenceTableData(BaseModel):
    activities: List[ActivityRead]
    centre_activities: List[CentreActivityResponse]
    preferences: List[CentreActivityPreferenceResponse]
    recommendations: List[CentreActivityRecommendationResponse]
    exclusions: List[CentreActivityExclusionResponse]
    patients: List[RefPatient]


class ActivityExclusionTableData(BaseModel):
    activities: List[ActivityRead]
    centre_activities: List[CentreActivityResponse]
    exclusions: List[CentreActivityExclusionResponse]
    patients: List[RefPatient]

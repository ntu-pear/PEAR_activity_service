from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.jwt_utils import get_current_user, JWTPayload
from app.schemas.aggregated_schema import ActivityPreferenceTableData, ActivityExclusionTableData
import app.crud.activity_crud as activity_crud
import app.crud.centre_activity_crud as centre_activity_crud
import app.crud.centre_activity_preference_crud as preference_crud
import app.crud.centre_activity_recommendation_crud as recommendation_crud
import app.crud.centre_activity_exclusion_crud as exclusion_crud
import app.crud.ref_patient_crud as patient_crud
from typing import Optional

router = APIRouter()


@router.get("/activity-preference-table", response_model=ActivityPreferenceTableData)
def get_activity_preference_table_data(
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
    include_deleted: bool = Query(False),
):
    activities = activity_crud.get_activities(db=db, include_deleted=include_deleted)
    centre_activities = centre_activity_crud.get_centre_activities(db=db, include_deleted=include_deleted)
    preferences = preference_crud.get_centre_activity_preferences(db=db, include_deleted=include_deleted)
    try:
        recommendations = recommendation_crud.get_all_centre_activity_recommendations(
            db=db,
            current_user_info={
                "id": current_user.userId if current_user else None,
                "role_name": current_user.roleName if current_user else None,
                "fullname": current_user.fullName if current_user else None,
                "bearer_token": ""
            },
            include_deleted=include_deleted
        )
    except Exception:
        recommendations = []
    exclusions = exclusion_crud.get_centre_activity_exclusions(db=db, include_deleted=include_deleted)
    patients, _, _ = patient_crud.get_ref_patients(db=db, page_no=0, page_size=10000)

    return ActivityPreferenceTableData(
        activities=activities,
        centre_activities=centre_activities,
        preferences=preferences,
        recommendations=recommendations,
        exclusions=exclusions,
        patients=patients,
    )


@router.get("/activity-preference-table/patient/{patient_id}", response_model=ActivityPreferenceTableData)
def get_activity_preference_table_data_by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
    include_deleted: bool = Query(False),
):
    patient = patient_crud.get_ref_patient_by_id(db=db, patient_id=str(patient_id))
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    activities = activity_crud.get_activities(db=db, include_deleted=include_deleted)
    centre_activities = centre_activity_crud.get_centre_activities(db=db, include_deleted=include_deleted)

    try:
        preferences = preference_crud.get_centre_activity_preferences_by_patient_id(
            db=db, patient_id=patient_id, include_deleted=include_deleted
        )
    except Exception:
        preferences = []

    try:
        all_recommendations = recommendation_crud.get_all_centre_activity_recommendations(
            db=db,
            current_user_info={
                "id": current_user.userId if current_user else None,
                "role_name": current_user.roleName if current_user else None,
                "fullname": current_user.fullName if current_user else None,
                "bearer_token": ""
            },
            include_deleted=include_deleted
        )
    except Exception:
        all_recommendations = []
    recommendations = [r for r in all_recommendations if r.patient_id == patient_id]

    exclusions = exclusion_crud.get_centre_activity_exclusions_by_patient_id(
        db=db, patient_id=patient_id, include_deleted=include_deleted
    )

    return ActivityPreferenceTableData(
        activities=activities,
        centre_activities=centre_activities,
        preferences=preferences,
        recommendations=recommendations,
        exclusions=exclusions,
        patients=[patient],
    )


@router.get("/activity-exclusion-table", response_model=ActivityExclusionTableData)
def get_activity_exclusion_table_data(
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
    include_deleted: bool = Query(False),
):
    activities = activity_crud.get_activities(db=db, include_deleted=include_deleted)
    centre_activities = centre_activity_crud.get_centre_activities(db=db, include_deleted=include_deleted)
    exclusions = exclusion_crud.get_centre_activity_exclusions(db=db, include_deleted=include_deleted)
    patients, _, _ = patient_crud.get_ref_patients(db=db, page_no=0, page_size=10000)

    return ActivityExclusionTableData(
        activities=activities,
        centre_activities=centre_activities,
        exclusions=exclusions,
        patients=patients,
    )


@router.get("/activity-exclusion-table/patient/{patient_id}", response_model=ActivityExclusionTableData)
def get_activity_exclusion_table_data_by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
    include_deleted: bool = Query(False),
):
    patient = patient_crud.get_ref_patient_by_id(db=db, patient_id=str(patient_id))
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    activities = activity_crud.get_activities(db=db, include_deleted=include_deleted)
    centre_activities = centre_activity_crud.get_centre_activities(db=db, include_deleted=include_deleted)
    exclusions = exclusion_crud.get_centre_activity_exclusions_by_patient_id(
        db=db, patient_id=patient_id, include_deleted=include_deleted
    )

    return ActivityExclusionTableData(
        activities=activities,
        centre_activities=centre_activities,
        exclusions=exclusions,
        patients=[patient],
    )

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.centre_activity_preference_crud as crud
import app.schemas.centre_activity_preference_schema as schemas
from app.auth.jwt_utils import get_current_user_with_flag, JWTPayload, is_supervisor, is_caregiver, optional_oauth2_scheme
from typing import Optional

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.CentreActivityPreferenceResponse,
    summary="Create Centre Activity Preference for Patients",
    description="Create Centre Activity Preference for Patients",
    status_code=status.HTTP_201_CREATED)
def create_centre_activity_preference(
    payload: schemas.CentreActivityPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    token: Optional[str] = Depends(optional_oauth2_scheme)
):
    # Check if Role is Supervisor or Caregiver
    if current_user and not (is_supervisor(current_user) or is_caregiver(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a Centre Activity Preference"
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
        "role_name": current_user.roleName if current_user else "Anonymous",
        "bearer_token": token if token else ""
    }
    return crud.create_centre_activity_preference(
        db=db,
        centre_activity_preference_data=payload,
        current_user_info=current_user_info,
    )

@router.get(
    "/",
    response_model=list[schemas.CentreActivityPreferenceResponse],
    summary="Get Centre Activity Preferences",
    description="Get Centre Activity Preferences",
    status_code=status.HTTP_200_OK)
def get_centre_activity_preferences(
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    include_deleted: bool = Query(False, description="Include deleted Centre Activity Preferences"),
):
    # Check if Role is Supervisor or Caregiver
    if current_user and not (is_supervisor(current_user) or is_caregiver(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view Centre Activity Preferences"
        )

    return crud.get_centre_activity_preferences(db=db)

@router.get(
    "/{centre_activity_preference_id}",
    response_model=schemas.CentreActivityPreferenceResponse,
    summary="Get Centre Activity Preference by ID",
    description="Get Centre Activity Preference by ID",
    status_code=status.HTTP_200_OK)
def get_centre_activity_preference_by_id(
    centre_activity_preference_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    include_deleted: bool = False,
):
    # Check if Role is Supervisor or Caregiver
    if current_user and not (is_supervisor(current_user) or is_caregiver(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this Centre Activity Preference"
        )
    
    return crud.get_centre_activity_preference_by_id(
        db=db,
        centre_activity_preference_id=centre_activity_preference_id,
        include_deleted=include_deleted,
    )

@router.get(
        "/patient/{patient_id}",
        response_model=list[schemas.CentreActivityPreferenceResponse],
        summary="Get Centre Activity Preference by Patient ID",
        description="Get Centre Activity Preference by Patient ID",
        status_code=status.HTTP_200_OK
)
def get_centre_activity_preferences_by_patient_id(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100,
):
    # Check if Role is Supervisor or Caregiver
    if current_user and not (is_supervisor(current_user) or is_caregiver(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view Centre Activity Preferences for this Patient"
        )

    return crud.get_centre_activity_preferences_by_patient_id(
        db=db,
        patient_id=patient_id,
        include_deleted=include_deleted,
        skip=skip,
        limit=limit,
    )

@router.put(
    "/{centre_activity_preference_id}",
    response_model=schemas.CentreActivityPreferenceResponse,
    summary="Update Centre Activity Preference by ID",
    description="Update Centre Activity Preference by ID",
    status_code=status.HTTP_200_OK)
def update_centre_activity_preference_by_id(
    payload: schemas.CentreActivityPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    token: Optional[str] = Depends(optional_oauth2_scheme)
):
    # Check if Role is Supervisor or Caregiver
    if current_user and not (is_supervisor(current_user) or is_caregiver(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this Centre Activity Preference"
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
        "role_name": current_user.roleName if current_user else "Anonymous",
        "bearer_token": token if token else ""
    }
    return crud.update_centre_activity_preference_by_id(
        db=db,
        centre_activity_preference_data=payload,
        current_user_info=current_user_info,
    )

@router.delete(
    "/{centre_activity_preference_id}",
    summary="Delete Centre Activity Preference by ID",
    description="Delete Centre Activity Preference by ID",
    response_model=schemas.CentreActivityPreferenceResponse
)
def delete_centre_activity_preference_by_id(
    centre_activity_preference_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    token: Optional[str] = Depends(optional_oauth2_scheme)
):
    # Check if Role is Supervisor or Caregiver
    if current_user and not (is_supervisor(current_user) or is_caregiver(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this Centre Activity Preference"
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
        "role_name": current_user.roleName if current_user else "Anonymous",
        "bearer_token": token if token else ""
    }
    return crud.delete_centre_activity_preference_by_id(
        db=db,
        centre_activity_preference_id=centre_activity_preference_id,
        current_user_info=current_user_info,
    )

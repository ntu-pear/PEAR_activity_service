from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.centre_activity_recommendation_crud as crud
import app.schemas.centre_activity_recommendation_schema as schemas
from app.auth.jwt_utils import get_current_user_with_flag, JWTPayload, is_doctor, optional_oauth2_scheme
from typing import Optional

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.CentreActivityRecommendationResponse,
    summary="Create Centre Activity Recommendation for Patients",
    description="Create Centre Activity Recommendation for Patients",
    status_code=status.HTTP_201_CREATED)
def create_centre_activity_recommendation(
    payload: schemas.CentreActivityRecommendationCreate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    token: Optional[str] = Depends(optional_oauth2_scheme)
):
    # Check if Role is Doctor
    if current_user and not is_doctor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to create a Centre Activity Recommendation {current_user.roleName if current_user else 'Anonymous'}"
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "role_name": current_user.roleName if current_user else None,
        "fullname": current_user.fullName if current_user else None,
        "bearer_token": token
    }
    
    return crud.create_centre_activity_recommendation(
        db=db,
        centre_activity_recommendation_data=payload,
        current_user_info=current_user_info
    )


@router.get(
    "/{centre_activity_recommendation_id}",
    response_model=schemas.CentreActivityRecommendationResponse,
    summary="Get Centre Activity Recommendation by ID",
    description="Get Centre Activity Recommendation by ID"
)
def get_centre_activity_recommendation_by_id(
    centre_activity_recommendation_id: int,
    include_deleted: bool = Query(False, description="Include deleted Centre Activity Recommendations"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    token: Optional[str] = Depends(optional_oauth2_scheme)
):
    # Check if Role is Doctor
    if current_user and not is_doctor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access Centre Activity Recommendations"
        )
    
    return crud.get_centre_activity_recommendation_by_id(
        db=db,
        centre_activity_recommendation_id=centre_activity_recommendation_id,
        include_deleted=include_deleted
    )


@router.get(
    "/",
    response_model=list[schemas.CentreActivityRecommendationResponse],
    summary="Get All Centre Activity Recommendations",
    description="Get All Centre Activity Recommendations"
)
def get_all_centre_activity_recommendations(
    include_deleted: bool = Query(False, description="Include deleted Centre Activity Recommendations"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    token: Optional[str] = Depends(optional_oauth2_scheme)
):
    # Check if Role is Doctor
    if current_user and not is_doctor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access Centre Activity Recommendations"
        )
    
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "role_name": current_user.roleName if current_user else None,
        "fullname": current_user.fullName if current_user else None,
        "bearer_token": token
    }
    
    return crud.get_all_centre_activity_recommendations(
        db=db,
        current_user_info=current_user_info,
        include_deleted=include_deleted
    )


@router.get(
    "/patient/{patient_id}",
    response_model=list[schemas.CentreActivityRecommendationResponse],
    summary="Get Centre Activity Recommendations by Patient ID",
    description="Get Centre Activity Recommendations for a specific Patient"
)
def get_centre_activity_recommendations_by_patient_id(
    patient_id: int,
    include_deleted: bool = Query(False, description="Include deleted Centre Activity Recommendations"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    token: Optional[str] = Depends(optional_oauth2_scheme)
):
    # Check if Role is Doctor
    if current_user and not is_doctor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access Centre Activity Recommendations"
        )
    
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "role_name": current_user.roleName if current_user else None,
        "fullname": current_user.fullName if current_user else None,
        "bearer_token": token
    }
    
    return crud.get_centre_activity_recommendations_by_patient_id(
        db=db,
        patient_id=patient_id,
        current_user_info=current_user_info,
        include_deleted=include_deleted
    )


@router.put(
    "/{centre_activity_recommendation_id}",
    response_model=schemas.CentreActivityRecommendationResponse,
    summary="Update Centre Activity Recommendation",
    description="Update Centre Activity Recommendation"
)
def update_centre_activity_recommendation(
    centre_activity_recommendation_id: int,
    payload: schemas.CentreActivityRecommendationUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    token: Optional[str] = Depends(optional_oauth2_scheme)
):
    # Check if Role is Doctor
    if current_user and not is_doctor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update Centre Activity Recommendations"
        )
    
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "role_name": current_user.roleName if current_user else None,
        "fullname": current_user.fullName if current_user else None,
        "bearer_token": token
    }
    
    # Set the ID in the payload for consistency
    payload.centre_activity_recommendation_id = centre_activity_recommendation_id
    
    return crud.update_centre_activity_recommendation(
        db=db,
        centre_activity_recommendation_data=payload,
        current_user_info=current_user_info
    )


@router.delete(
    "/{centre_activity_recommendation_id}",
    response_model=schemas.CentreActivityRecommendationResponse,
    summary="Delete Centre Activity Recommendation",
    description="Delete Centre Activity Recommendation (Soft Delete)"
)
def delete_centre_activity_recommendation(
    centre_activity_recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    token: Optional[str] = Depends(optional_oauth2_scheme)
):
    # Check if Role is Doctor
    if current_user and not is_doctor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete Centre Activity Recommendations"
        )
    
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "role_name": current_user.roleName if current_user else None,
        "fullname": current_user.fullName if current_user else None,
        "bearer_token": token
    }
    
    return crud.delete_centre_activity_recommendation(
        db=db,
        centre_activity_recommendation_id=centre_activity_recommendation_id,
        current_user_info=current_user_info
    )

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
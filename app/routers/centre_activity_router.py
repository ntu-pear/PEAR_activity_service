from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.centre_activity_crud import (
    create_centre_activity,
    get_centre_activity_by_id,
    get_centre_activities,
    update_centre_activity, 
    delete_centre_activity,
)
from app.schemas.centre_activity_schema import (
    CentreActivityCreate,
    CentreActivityUpdate,
    CentreActivityResponse,
)
from app.auth.jwt_utils import get_current_user, JWTPayload

router = APIRouter()

@router.post("/", response_model=CentreActivityResponse, description="Create a new Centre Activity", status_code=status.HTTP_201_CREATED)
def create_centre_activity(
    centre_activity: CentreActivityCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # Optional JWT for Swagger testing
):
    user_full_name = getattr(current_user, 'fullName', 'Anonymous User') if current_user else 'Anonymous User'
    return create_centre_activity(
        db=db,
        centre_activity_data=centre_activity,
        user_full_name=user_full_name
    )

@router.get("/", response_model=list[CentreActivityResponse])
def list_activities(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return get_centre_activities(db)

@router.get("/{centre_activity_id}", response_model=CentreActivityResponse)
def get_by_id(
    centre_activity_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return get_centre_activity_by_id(db, centre_activity_id)

@router.put("/", response_model=CentreActivityResponse)
def update(
    centre_activity: CentreActivityUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_full_name = getattr(current_user, 'fullName', 'Anonymous User') if current_user else 'Anonymous User'
    return update_centre_activity(
        db=db,
        centre_activity_data=centre_activity,
        user_full_name=user_full_name
    )

@router.delete("/{centre_activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    centre_activity_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_id = getattr(current_user, 'userId', 'system') if current_user else 'system'
    user_full_name = getattr(current_user, 'fullName', 'Anonymous User') if current_user else 'Anonymous User'
    delete_centre_activity(
        db=db,
        centre_activity_id=centre_activity_id,
        modified_by_id=user_id,
        user_full_name=user_full_name
    )
    return None

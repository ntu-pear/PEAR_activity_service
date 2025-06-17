from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.centre_activity_crud as crud 
import app.schemas.centre_activity_schema as schemas
from app.auth.jwt_utils import get_current_user_with_flag, JWTPayload

router = APIRouter()

@router.post(
        "/", 
        response_model=schemas.CentreActivityResponse, 
        summary="Create Centre Activity",
        description="Create Centre Activity", 
        status_code=status.HTTP_201_CREATED)
def create_centre_activity(
    payload: schemas.CentreActivityCreate,
    db: Session = Depends(get_db),
    #current_user = Depends(get_current_user_with_flag)  # Optional JWT for Swagger testing
):
    #user_full_name = getattr(current_user, 'fullName', 'Anonymous User') if current_user else 'Anonymous User'
    
    return crud.create_centre_activity(
        db=db,
        centre_activity_data=payload,
        #user_full_name=user_full_name
    )


@router.get(
        "/", 
        summary="List Centre Activities",
        description="List all Centre Activities",
        response_model=list[schemas.CentreActivityResponse])
def list_activities(
    db: Session = Depends(get_db),
    #current_user = Depends(get_current_user_with_flag)
):
    return crud.get_centre_activities(db)


@router.get(
        "/{centre_activity_id}", 
        summary="Get Centre Activity by ID",
        description="Get a specific Centre Activity by its ID",
        response_model=schemas.CentreActivityResponse)
def get_by_id(
    centre_activity_id: int,
    db: Session = Depends(get_db),
   # current_user = Depends(get_current_user_with_flag)
):
    return crud.get_centre_activity_by_id(db, centre_activity_id)


@router.put(
        "/", 
        summary="Update Centre Activity",
        description="Update an existing Centre Activity",
        response_model=schemas.CentreActivityResponse)
def update(
    centre_activity: schemas.CentreActivityUpdate,
    db: Session = Depends(get_db),
    #current_user = Depends(get_current_user_with_flag)
):
    #user_full_name = getattr(current_user, 'fullName', 'Anonymous User') if current_user else 'Anonymous User'
    return crud.update_centre_activity(
        db=db,
        centre_activity_data=centre_activity,
        #user_full_name=user_full_name
    )


@router.delete(
        "/{centre_activity_id}", 
        summary="Delete Centre Activity",
        description="Delete a Centre Activity by its ID",
        response_model=schemas.CentreActivityResponse
        )
def delete(
    centre_activity_id: int,
    modified_by_id: str = Query(..., description="ID of the user modifying the record"),    # To be replaced with JWT auth
    #user_full_name: str = Query(..., description="Full name of the user"),                  # To be replaced with JWT auth
    db: Session = Depends(get_db),
    #current_user = Depends(get_current_user_with_flag)
):
    return crud.delete_centre_activity(
        db=db,
        centre_activity_id=centre_activity_id,
        modified_by_id=modified_by_id,
        #user_full_name=user_full_name
    )

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.centre_activity_crud as crud 
import app.schemas.centre_activity_schema as schemas
from app.auth.jwt_utils import get_current_user_with_flag, JWTPayload, is_supervisor
from typing import Optional

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
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a Centre Activity."
        )
    
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }
    return crud.create_centre_activity(
        db=db,
        centre_activity_data=payload,
        current_user_info=current_user_info,
    )


@router.get(
        "/", 
        summary="List Centre Activities",
        description="List all Centre Activities",
        response_model=list[schemas.CentreActivityResponse])
def list_activities(
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    include_deleted: bool = Query(False, description="Include soft-deleted records"),
    skip: int = 0,
    limit: int = 100,
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view Centre Activities."
        )
    return crud.get_centre_activities(db, include_deleted=include_deleted)


@router.get(
        "/{centre_activity_id}", 
        summary="Get Centre Activity by ID",
        description="Get a specific Centre Activity by its ID",
        response_model=schemas.CentreActivityResponse)
def get_by_id(
    centre_activity_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    include_deleted: bool = Query(False, description="Include soft-deleted records")
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view a Centre Activity."
        )
    return crud.get_centre_activity_by_id(db, centre_activity_id, include_deleted=include_deleted)


@router.put(
        "/", 
        summary="Update Centre Activity",
        description="Update an existing Centre Activity",
        response_model=schemas.CentreActivityResponse)
def update(
    centre_activity: schemas.CentreActivityUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update a Centre Activity."
        )
    
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }
    return crud.update_centre_activity(
        db=db,
        centre_activity_data=centre_activity,
        current_user_info=current_user_info
    )


@router.delete(
        "/{centre_activity_id}", 
        summary="Delete Centre Activity",
        description="Delete a Centre Activity by its ID",
        response_model=schemas.CentreActivityResponse
        )
def delete(
    centre_activity_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete a Centre Activity."
        )
    
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }

    return crud.delete_centre_activity(
        db=db,
        centre_activity_id=centre_activity_id,
        current_user_info=current_user_info
    )

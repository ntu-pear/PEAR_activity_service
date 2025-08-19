from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.auth.jwt_utils import get_current_user, JWTPayload, is_supervisor

import app.crud.activity_crud as crud
import app.schemas.activity_schema as schemas
from app.database import get_db

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.ActivityRead,
    status_code=status.HTTP_201_CREATED
)
def create_activity(
    payload: schemas.ActivityCreate,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create an Activity."
        )
    user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }
    return crud.create_activity(db=db, activity_in=payload, current_user_info=user_info)

@router.get(
    "/",
    response_model=List[schemas.ActivityRead]
)
def list_activities(
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
    include_deleted: bool = Query(False, description="Include soft‑deleted records"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, gt=0, le=1000, description="Max records to return"),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view Activities."
        )
    return crud.get_activities(
        db=db,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted
    )

@router.get(
    "/{activity_id}",
    response_model=schemas.ActivityRead
)
def get_activity_by_id(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
    include_deleted: bool = Query(False, description="Include soft‑deleted records"),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this Activity."
        )
    obj = crud.get_activity_by_id(
        db=db,
        activity_id=activity_id,
        include_deleted=include_deleted
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Activity not found")
    return obj

@router.put(
    "/{activity_id}",
    response_model=schemas.ActivityRead
)
def update_activity_by_id(
    activity_in: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update an Activity."
        )
    user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }
    return crud.update_activity_by_id(
        db=db,
        activity_id=activity_in.id,
        activity_in=activity_in,
        current_user_info=user_info
    )

@router.delete(
    "/{activity_id}",
    response_model=schemas.ActivityRead,
    summary="Delete an activity",
)
def delete_activity_by_id(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: JWTPayload = Depends(get_current_user),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete an Activity."
        )
    user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }
    return crud.delete_activity_by_id(
        db=db,
        activity_id=activity_id,
        current_user_info=user_info
    )
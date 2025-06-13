from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

import app.crud.activity_crud as crud
import app.schemas.activity_schema as schemas
from app.database import get_db

router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)

@router.post(
    "/",
    response_model=schemas.ActivityRead,
    status_code=status.HTTP_201_CREATED
)
def create_activity(
    payload: schemas.ActivityCreate,
    db: Session = Depends(get_db),
):
    return crud.create_activity(db=db, activity_in=payload)

@router.get(
    "/",
    response_model=List[schemas.ActivityRead]
)
def list_activities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.get_activities(db=db, skip=skip, limit=limit)

@router.get(
    "/{activity_id}",
    response_model=schemas.ActivityRead
)
def get_activity_by_id(
    activity_id: int,
    db: Session = Depends(get_db),
):
    obj = crud.get_activity_by_id(db=db, activity_id=activity_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    return obj

@router.put(
    "/{activity_id}",
    response_model=schemas.ActivityRead
)
def update_activity_by_id(
    activity_id: int,
    payload: schemas.ActivityCreate,
    db: Session = Depends(get_db),
):
    return crud.update_activity_by_id(
        db=db,
        activity_id=activity_id,
        activity_in=payload
    )

@router.delete(
    "/{activity_id}",
    response_model=schemas.ActivityRead,
    summary="Delete an activity",
)
def delete_activity_by_id(
    activity_id: int,
    db: Session = Depends(get_db),
):
    return crud.delete_activity_by_id(
        db=db,
        activity_id=activity_id
    )
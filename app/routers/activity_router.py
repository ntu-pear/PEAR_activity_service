from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

import app.crud.activity_crud as crud
import app.schemas.activity as schemas
from app.utils.database import get_db

router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)

@router.post("/", response_model=schemas.Activity, status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: schemas.ActivityCreate,
    db: Session = Depends(get_db),
):
    return crud.create_activity(db, payload)

@router.get("/", response_model=List[schemas.Activity])
def list_activities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.get_activities(db, skip, limit)

@router.get("/{activity_id}", response_model=schemas.Activity)
def get_activity(
    activity_id: str,
    db: Session = Depends(get_db),
):
    obj = crud.get_activity(db, activity_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj

@router.put("/{activity_id}", response_model=schemas.Activity)
def update_activity(
    activity_id: str,
    payload: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
):
    if payload.id != activity_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    return crud.update_activity(db, payload)

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: str,
    db: Session = Depends(get_db),
):
    crud.delete_activity(db, activity_id)
    return
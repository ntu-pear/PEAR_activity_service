from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.models.activity_model as models
import app.schemas.activity_schema as schemas

def get_activity_by_id(db: Session, *, activity_id: int) -> Optional[models.Activity]:
    return (
        db.query(models.Activity)
          .filter(
              models.Activity.id == activity_id,
              models.Activity.active == True,
              models.Activity.is_deleted == False,
          )
          .first()
    )

def get_activities(db: Session, *, skip: int = 0, limit: int = 100) -> List[models.Activity]:
    return (
        db.query(models.Activity)
          .filter(
              models.Activity.active == True,
              models.Activity.is_deleted == False,
          )
          .order_by(models.Activity.id)       
          .offset(skip)
          .limit(limit)
          .all()
    )

def create_activity(db: Session, *, activity_in: schemas.ActivityCreate) -> models.Activity:
    # duplicate‐title check 
    existing = (
        db.query(models.Activity)
          .filter(
                models.Activity.title == activity_in.title,              models.Activity.active == True,
                models.Activity.is_deleted == False,
          )
          .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity already exists"
        )
    # end_date ≥ start_date check 
    if activity_in.end_date and activity_in.end_date < activity_in.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date cannot be earlier than start_date"
        )
    obj = models.Activity(**activity_in.model_dump(by_alias=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_activity_by_id(db: Session, *, activity_id: int, activity_in: schemas.ActivityCreate) -> models.Activity:
    obj = get_activity_by_id(db, activity_id=activity_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    update_data = activity_in.model_dump(by_alias=True, exclude_unset=True)
    new_start = update_data.get("start_date", obj.start_date)
    new_end   = update_data.get("end_date",   obj.end_date)
    if new_end and new_end < new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date cannot be earlier than start_date"
        )
    for field, value in update_data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj

def delete_activity_by_id(db: Session, *, activity_id: int) -> models.Activity:
    obj = get_activity_by_id(db, activity_id=activity_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or already deleted"
        )
    obj.is_deleted = True
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
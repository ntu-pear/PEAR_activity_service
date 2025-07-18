from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.models.activity_model as models
import app.schemas.activity_schema as schemas

def get_activity_by_id(
    db: Session, *, activity_id: int, include_deleted: bool = False
) -> Optional[models.Activity]:
    query = db.query(models.Activity).filter(models.Activity.id == activity_id)
    if not include_deleted:
        query = query.filter(models.Activity.is_deleted == False)
    return query.first()

def get_activities(
    db: Session, *, skip: int = 0, limit: int = 100, include_deleted: bool = False
) -> List[models.Activity]:
    query = db.query(models.Activity)

    # Exclude is_deleted=True records, else show all records if include_deleted is True
    if not include_deleted:
        query = query.filter(models.Activity.is_deleted == False)
    return (
        query.order_by(models.Activity.id)
             .offset(skip)
             .limit(limit)
             .all()
    )

def create_activity(db: Session, *, activity_in: schemas.ActivityCreate) -> models.Activity:
    # duplicate‐title check 
    existing = (
        db.query(models.Activity)
          .filter(
                models.Activity.title == activity_in.title,
                models.Activity.is_deleted == False,
          )
          .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity already exists"
        )

    obj = models.Activity(**activity_in.model_dump(by_alias=True))
    db.add(obj)
    try:    
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database commit failed")
    return obj

def update_activity_by_id(db: Session, *, activity_id: int, activity_in: schemas.ActivityCreate) -> models.Activity:
    obj = get_activity_by_id(db, activity_id=activity_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    update_data = activity_in.model_dump(by_alias=True, exclude_unset=True)

    for field, value in update_data.items():
        setattr(obj, field, value)

    try:
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database commit failed")
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
    try:
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database commit failed")
    return obj
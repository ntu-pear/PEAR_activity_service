from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import app.models.activity_model as models
import app.schemas.activity as schemas

def get_activity(db: Session, activity_id: str):
    return db.query(models.Activity)\
             .filter(models.Activity.id == activity_id)\
             .first()

def get_activities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Activity).offset(skip).limit(limit).all()

def create_activity(db: Session, obj_in: schemas.ActivityCreate):
    db_obj = models.Activity(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_activity(db: Session, obj_in: schemas.ActivityUpdate):
    db_obj = get_activity(db, obj_in.id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Activity not found")
    for field, val in obj_in.dict(exclude_unset=True).items():
        setattr(db_obj, field, val)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_activity(db: Session, activity_id: str):
    db_obj = get_activity(db, activity_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Activity not found")
    db.delete(db_obj)
    db.commit()
    return

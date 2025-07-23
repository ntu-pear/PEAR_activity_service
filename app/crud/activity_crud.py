from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict

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

def create_activity(
    db: Session,
    *,
    activity_in: schemas.ActivityCreate,
    current_user_info: dict
) -> models.Activity:
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
    obj.created_by_id = current_user_info.get("id")
    obj.modified_by_id = current_user_info.get("id")
    db.add(obj)
    try:    
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database commit failed")
    
    updated = serialize_data(activity_in.model_dump())
    log_crud_action(
        action=ActionType.CREATE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Created a new Activity",
        table="ACTIVITY",
        entity_id=obj.id,
        original_data=None,
        updated_data=updated,
    )
    return obj

def update_activity_by_id(
    db: Session,
    *,
    activity_id: int,
    activity_in: schemas.ActivityUpdate,
    current_user_info: dict
) -> models.Activity:
    obj = get_activity_by_id(db, activity_id=activity_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    original = serialize_data(model_to_dict(obj))
    update_data = activity_in.model_dump(by_alias=True, exclude_unset=True)
    update_data["modified_by_id"] = current_user_info.get("id")

    for field, value in update_data.items():
        setattr(obj, field, value)

    try:
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database commit failed")
    
    log_crud_action(
        action=ActionType.UPDATE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Updated an Activity",
        table="ACTIVITY",
        entity_id=obj.id,
        original_data=original,
        updated_data=serialize_data(update_data),
    )
    return obj

def delete_activity_by_id(
    db: Session,
    *,
    activity_id: int,
    current_user_info: dict
) -> models.Activity:
    obj = get_activity_by_id(db, activity_id=activity_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or already deleted"
        )
    
    original = serialize_data(model_to_dict(obj))
    obj.is_deleted = True
    obj.modified_by_id = current_user_info.get("id")

    try:
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database commit failed")

    log_crud_action(
        action=ActionType.DELETE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Deleted an Activity",
        table="ACTIVITY",
        entity_id=obj.id,
        original_data=original,
        updated_data=None,
    )
    return obj
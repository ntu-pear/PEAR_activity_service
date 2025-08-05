from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import app.models.activity_exclusion_model as models
import app.schemas.activity_exclusion_schema as schemas
from app.crud.activity_crud import get_activity_by_id
from app.services.patient_service import get_patient_by_id
from app.logger.logger_utils import (
    log_crud_action, ActionType, serialize_data, model_to_dict
)
from typing import List

def get_exclusion_by_id(
    db: Session,
    exclusion_id: int,
    include_deleted: bool = False
) -> models.ActivityExclusion:
    q = db.query(models.ActivityExclusion).filter(models.ActivityExclusion.id == exclusion_id)
    if not include_deleted:
        q = q.filter(models.ActivityExclusion.is_deleted == False)
    obj = q.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Activity Exclusion not found")
    return obj

def get_exclusions(
    db: Session,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[models.ActivityExclusion]:
    q = db.query(models.ActivityExclusion)
    if not include_deleted:
        q = q.filter(models.ActivityExclusion.is_deleted == False)
    return (
        q.order_by(models.ActivityExclusion.id)
         .offset(skip)
         .limit(limit)
         .all()
    )

def create_exclusion(
    db: Session,
    exclusion_data: schemas.ActivityExclusionCreate,
    current_user_info: dict
) -> models.ActivityExclusion:
    # 1) Validate activity exists
    if not get_activity_by_id(db, activity_id=exclusion_data.activity_id):
        raise HTTPException(status_code=404, detail="Activity not found")

    # 2) Validate patient exists (via external service)
    try:
        get_patient_by_id(require_auth=False, bearer_token="", patient_id=exclusion_data.patient_id)
    except HTTPException:
        raise HTTPException(status_code=400, detail="Invalid Patient ID")

    obj = models.ActivityExclusion(**exclusion_data.model_dump())
    obj.created_by_id  = current_user_info["id"]
    obj.modified_by_id = current_user_info["id"]
    db.add(obj)
    try:
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating exclusion: {e}")

    log_crud_action(
        action=ActionType.CREATE,
        user=current_user_info["id"],
        user_full_name=current_user_info.get("fullname"),
        message="Created Activity Exclusion",
        table="ACTIVITY_EXCLUSION",
        entity_id=obj.id,
        original_data=None,
        updated_data=serialize_data(model_to_dict(obj))
    )
    return obj

def update_exclusion(
    db: Session,
    exclusion_data: schemas.ActivityExclusionUpdate,
    current_user_info: dict
) -> models.ActivityExclusion:
    db_obj = get_exclusion_by_id(db, exclusion_data.id, include_deleted=True)
    original = serialize_data(model_to_dict(db_obj))

    if exclusion_data.activity_id is not None:
        if not get_activity_by_id(db, activity_id=exclusion_data.activity_id):
            raise HTTPException(status_code=404, detail="Activity not found")
        db_obj.activity_id = exclusion_data.activity_id

    if exclusion_data.patient_id is not None:
        try:
            get_patient_by_id(require_auth=False, bearer_token="", patient_id=exclusion_data.patient_id)
        except HTTPException:
            raise HTTPException(status_code=400, detail="Invalid Patient ID")
        db_obj.patient_id = exclusion_data.patient_id

    # update all other fields if provided
    update_data = exclusion_data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_obj, k, v)

    try:
        db.commit()
        db.refresh(db_obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating exclusion: {e}")

    log_crud_action(
        action=ActionType.UPDATE,
        user=current_user_info["id"],
        user_full_name=current_user_info.get("fullname"),
        message="Updated Activity Exclusion",
        table="ACTIVITY_EXCLUSION",
        entity_id=db_obj.id,
        original_data=original,
        updated_data=serialize_data(model_to_dict(db_obj))
    )
    return db_obj

def delete_exclusion(
    db: Session,
    exclusion_id: int,
    current_user_info: dict
) -> models.ActivityExclusion:
    obj = get_exclusion_by_id(db, exclusion_id)
    original = serialize_data(model_to_dict(obj))
    obj.is_deleted     = True
    obj.modified_by_id = current_user_info["id"]
    try:
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting exclusion: {e}")

    log_crud_action(
        action=ActionType.DELETE,
        user=current_user_info["id"],
        user_full_name=current_user_info.get("fullname"),
        message="Deleted Activity Exclusion",
        table="ACTIVITY_EXCLUSION",
        entity_id=obj.id,
        original_data=original,
        updated_data=None
    )
    return obj
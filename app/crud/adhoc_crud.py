from sqlalchemy.orm import Session
import app.models.adhoc_model as models
import app.schemas.adhoc_schema as schemas
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.services.patient_service import get_patient_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from fastapi import HTTPException
from typing import List
from datetime import datetime

def get_adhoc_by_id(
    db: Session,
    adhoc_id: int,
    include_deleted: bool = False
) -> models.Adhoc:
    if include_deleted:
        adhoc = (db.query(models.Adhoc).filter(models.Adhoc.id == adhoc_id).first())
    else:
        adhoc = (db.query(models.Adhoc).filter(models.Adhoc.id == adhoc_id, models.Adhoc.is_deleted == False).first())
    if not adhoc:
        raise HTTPException(status_code=404, detail="Adhoc record not found")
    return adhoc

def get_adhocs_by_patient_id(
    db: Session,
    patient_id: int,
    include_deleted: bool = False,
) -> list[models.Adhoc]:
    q = db.query(models.Adhoc).filter(models.Adhoc.patient_id == patient_id)
    if not include_deleted:
        q = q.filter(models.Adhoc.is_deleted == False)
    q = q.order_by(models.Adhoc.id)
    results = q.all()
    if not results:
        raise HTTPException(status_code=404, detail="No Adhoc records for this patient")
    return results

def get_adhocs(
    db: Session,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[models.Adhoc]:
    query = db.query(models.Adhoc)
    if not include_deleted:
        query = query.filter(models.Adhoc.is_deleted == False)
    query = query.order_by(models.Adhoc.id)
    adhocs = query.offset(skip).limit(limit).all()
    if not adhocs:
        raise HTTPException(status_code=404, detail="No Adhoc records found")
    return adhocs

def create_adhoc(
    db: Session,
    adhoc_data: schemas.AdhocCreate,
    current_user_info: dict
) -> models.Adhoc:
    # validate referenced centre_activities
    old_ca = get_centre_activity_by_id(db, centre_activity_id=adhoc_data.old_centre_activity_id)
    if not old_ca:
        raise HTTPException(status_code=404, detail="Old centre activity not found")

    new_ca = get_centre_activity_by_id(db, centre_activity_id=adhoc_data.new_centre_activity_id)
    if not new_ca:
        raise HTTPException(status_code=404, detail="New centre activity not found")
    
    # validate patient
    try:
        get_patient_by_id(require_auth=False, bearer_token="", patient_id=adhoc_data.patient_id)
    except HTTPException as e:
        raise HTTPException(status_code=400, detail="Invalid Patient ID") from e

    db_adhoc = models.Adhoc(**adhoc_data.model_dump())
    try:
        db.add(db_adhoc)
        db.commit()
        db.refresh(db_adhoc)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Adhoc record: {e}")

    log_crud_action(
        action=ActionType.CREATE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Created Adhoc record",
        table="ADHOC",
        entity_id=db_adhoc.id,
        original_data=None,
        updated_data=serialize_data(model_to_dict(db_adhoc))
    )
    return db_adhoc

def update_adhoc(
    db: Session,
    adhoc_data: schemas.AdhocUpdate,
    current_user_info: dict
) -> models.Adhoc:
    db_adhoc = db.query(models.Adhoc).filter(models.Adhoc.id == adhoc_data.id).first()
    if not db_adhoc:
        raise HTTPException(status_code=404, detail="Adhoc record not found")

    original = serialize_data(model_to_dict(db_adhoc))

    if adhoc_data.old_centre_activity_id is not None:
        get_centre_activity_by_id(db, centre_activity_id=adhoc_data.old_centre_activity_id)
        db_adhoc.old_centre_activity_id = adhoc_data.old_centre_activity_id
    if adhoc_data.new_centre_activity_id is not None:
        get_centre_activity_by_id(db, centre_activity_id=adhoc_data.new_centre_activity_id)
        db_adhoc.new_centre_activity_id = adhoc_data.new_centre_activity_id

    # validate patient
    try:
        get_patient_by_id(require_auth=False, bearer_token="", patient_id=adhoc_data.patient_id)
    except HTTPException as e:
        raise HTTPException(status_code=400, detail="Invalid Patient ID") from e
    db_adhoc.patient_id = adhoc_data.patient_id

    db_adhoc.status = adhoc_data.status
    db_adhoc.start_date = adhoc_data.start_date
    db_adhoc.end_date = adhoc_data.end_date
    db_adhoc.is_deleted = adhoc_data.is_deleted
    # stamp modification
    db_adhoc.modified_date = adhoc_data.modified_date or datetime.utcnow()
    db_adhoc.modified_by_id = adhoc_data.modified_by_id

    try:
        db.commit()
        db.refresh(db_adhoc)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Adhoc record: {e}")

    updated = serialize_data(model_to_dict(db_adhoc))
    log_crud_action(
        action=ActionType.UPDATE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Updated Adhoc record",
        table="ADHOC",
        entity_id=db_adhoc.id,
        original_data=original,
        updated_data=updated
    )
    return db_adhoc

def delete_adhoc(
    db: Session,
    adhoc_id: int,
    current_user_info: dict
) -> models.Adhoc:
    db_adhoc = db.query(models.Adhoc).filter(models.Adhoc.id == adhoc_id).first()
    if not db_adhoc:
        raise HTTPException(status_code=404, detail="Adhoc record not found")

    original = serialize_data(model_to_dict(db_adhoc))
    db_adhoc.is_deleted = True
    db_adhoc.modified_date = datetime.utcnow()
    db_adhoc.modified_by_id = current_user_info.get("id")

    try:
        db.commit()
        db.refresh(db_adhoc)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Adhoc record: {e}")

    log_crud_action(
        action=ActionType.DELETE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Deleted Adhoc record",
        table="ADHOC",
        entity_id=db_adhoc.id,
        original_data=original,
        updated_data=None
    )
    return db_adhoc
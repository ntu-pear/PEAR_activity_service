from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
import app.models.routine_exclusion_model as models
import app.schemas.routine_exclusion_schema as schemas
from app.crud.routine_crud import get_routine_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict

def _check_for_overlapping_exclusion(
    db: Session,
    exclusion_data: schemas.RoutineExclusionBase,
    exclude_id: int = None
):
    query = db.query(models.RoutineExclusion).filter(
        models.RoutineExclusion.routine_id == exclusion_data.routine_id,
        models.RoutineExclusion.is_deleted == False,
        models.RoutineExclusion.start_date <= exclusion_data.end_date,
        models.RoutineExclusion.end_date >= exclusion_data.start_date
    )
    
    if exclude_id is not None:
        query = query.filter(models.RoutineExclusion.id != exclude_id)
    
    existing_exclusion = query.first()
    
    if existing_exclusion:
        raise HTTPException(
            status_code=409,
            detail="An overlapping exclusion already exists for this routine."
        )

def _validate_routine_exclusion_data(db: Session, exclusion_data: schemas.RoutineExclusionBase):
    routine = get_routine_by_id(db, routine_id=exclusion_data.routine_id)
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine with ID {exclusion_data.routine_id} not found")
    
    if routine.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot create exclusion for a deleted routine")

def create_routine_exclusion(
    db: Session,
    exclusion_data: schemas.RoutineExclusionCreate,
    current_user_info: dict
):
    current_user_id = current_user_info.get("id")
    
    _check_for_overlapping_exclusion(db, exclusion_data)
    _validate_routine_exclusion_data(db, exclusion_data)
    
    db_exclusion = models.RoutineExclusion(**exclusion_data.model_dump())
    db_exclusion.created_by_id = current_user_id
    db_exclusion.created_date = datetime.now()
    db.add(db_exclusion)
    
    try:
        db.commit()
        db.refresh(db_exclusion)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Routine Exclusion record: {e}")
    
    updated_data_dict = serialize_data(exclusion_data.model_dump())
    
    log_crud_action(
        action=ActionType.CREATE,
        user=current_user_id,
        user_full_name=current_user_info.get("fullname"),
        message="Created Routine Exclusion record",
        table="ROUTINE_EXCLUSION",
        entity_id=db_exclusion.id,
        original_data=None,
        updated_data=updated_data_dict
    )
    
    return db_exclusion

def get_routine_exclusion_by_id(
    db: Session,
    exclusion_id: int,
    include_deleted: bool = False
):
    if include_deleted:
        db_exclusion = db.query(models.RoutineExclusion).filter(models.RoutineExclusion.id == exclusion_id).first()
    else:
        db_exclusion = db.query(models.RoutineExclusion).filter(
            models.RoutineExclusion.id == exclusion_id,
            models.RoutineExclusion.is_deleted == False
        ).first()
    
    if not db_exclusion:
        raise HTTPException(status_code=404, detail="Routine Exclusion record not found")
    
    return db_exclusion

def get_routine_exclusions(
    db: Session,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.RoutineExclusion)
    if not include_deleted:
        query = query.filter(models.RoutineExclusion.is_deleted == False)
    query = query.order_by(models.RoutineExclusion.start_date.asc())
    exclusions = query.offset(skip).limit(limit).all()
    if not exclusions:
        raise HTTPException(status_code=404, detail="No Routine Exclusion records found")
    return exclusions

def get_routine_exclusions_by_routine_id(
    db: Session,
    routine_id: int,
    include_deleted: bool = False
):
    query = db.query(models.RoutineExclusion).filter(models.RoutineExclusion.routine_id == routine_id)
    if not include_deleted:
        query = query.filter(models.RoutineExclusion.is_deleted == False)
    query = query.order_by(models.RoutineExclusion.start_date.asc())
    results = query.all()
    if not results:
        raise HTTPException(status_code=404, detail="No Routine Exclusion records for this routine")
    return results

def update_routine_exclusion(
    db: Session,
    exclusion_data: schemas.RoutineExclusionUpdate,
    current_user_info: dict
):
    db_exclusion = db.query(models.RoutineExclusion).filter(models.RoutineExclusion.id == exclusion_data.id).first()
    
    if not db_exclusion:
        raise HTTPException(status_code=404, detail="Routine Exclusion record not found")
    
    _check_for_overlapping_exclusion(db, exclusion_data, exclude_id=exclusion_data.id)
    _validate_routine_exclusion_data(db, exclusion_data)
    
    original_data_dict = serialize_data(model_to_dict(db_exclusion))
    
    db_exclusion.routine_id = exclusion_data.routine_id
    db_exclusion.start_date = exclusion_data.start_date
    db_exclusion.end_date = exclusion_data.end_date
    db_exclusion.remarks = exclusion_data.remarks
    db_exclusion.modified_by_id = current_user_info.get("id")
    db_exclusion.modified_date = datetime.now()
    
    try:
        db.commit()
        db.refresh(db_exclusion)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Routine Exclusion record: {e}")
    
    updated_data_dict = serialize_data(model_to_dict(db_exclusion))
    
    log_crud_action(
        action=ActionType.UPDATE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Updated Routine Exclusion record",
        table="ROUTINE_EXCLUSION",
        entity_id=db_exclusion.id,
        original_data=original_data_dict,
        updated_data=updated_data_dict
    )
    
    return db_exclusion

def delete_routine_exclusion(
    db: Session,
    exclusion_id: int,
    current_user_info: dict
):
    db_exclusion = db.query(models.RoutineExclusion).filter(models.RoutineExclusion.id == exclusion_id).first()
    
    if not db_exclusion:
        raise HTTPException(status_code=404, detail="Routine Exclusion record not found")
    
    original_data_dict = serialize_data(model_to_dict(db_exclusion))
    
    db_exclusion.is_deleted = True
    db_exclusion.modified_by_id = current_user_info.get("id")
    db_exclusion.modified_date = datetime.now()
    
    try:
        db.commit()
        db.refresh(db_exclusion)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Routine Exclusion record: {e}")
    
    log_crud_action(
        action=ActionType.DELETE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Deleted Routine Exclusion record",
        table="ROUTINE_EXCLUSION",
        entity_id=db_exclusion.id,
        original_data=original_data_dict,
        updated_data=None
    )
    
    return db_exclusion

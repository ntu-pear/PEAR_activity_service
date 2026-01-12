from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
import app.models.routine_model as models
import app.schemas.routine_schema as schemas
from app.crud.activity_crud import get_activity_by_id
from app.services.patient_service import get_patient_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict

def _check_for_duplicate_routine(
    db: Session,
    routine_data: schemas.RoutineCreate,
    exclude_id: int = None
):
    # day_of_week is a bitmask: Monday=1, Tuesday=2, Wednesday=4, Thursday=8, Friday=16, Saturday=32, Sunday=64
    query = db.query(models.Routine).filter(
        models.Routine.patient_id == routine_data.patient_id,
        models.Routine.activity_id == routine_data.activity_id,
        models.Routine.is_deleted == False,
        (models.Routine.day_of_week.op('&')(routine_data.day_of_week)) != 0,
        models.Routine.start_time < routine_data.end_time,
        models.Routine.end_time > routine_data.start_time,
        models.Routine.start_date <= routine_data.end_date,
        models.Routine.end_date >= routine_data.start_date
    )
    
    if exclude_id is not None:
        query = query.filter(models.Routine.id != exclude_id)
    
    existing_routine = query.first()
    
    if existing_routine:
        raise HTTPException(
            status_code=409,
            detail="A routine with overlapping days and times already exists for this patient and activity."
        )

def _validate_routine_data(db: Session, routine_data: schemas.RoutineCreate, bearer_token: str = None):
    activity = get_activity_by_id(db, activity_id=routine_data.activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail=f"Activity with ID {routine_data.activity_id} not found")
    
    if activity.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot create routine for a deleted activity")
    
    try:
        get_patient_by_id(
            require_auth=True,
            bearer_token=bearer_token or "",
            patient_id=routine_data.patient_id,
        )
    except HTTPException as e:
        raise HTTPException(status_code=400, detail="Invalid Patient ID") from e

def create_routine(
    db: Session,
    routine_data: schemas.RoutineCreate,
    current_user_info: dict
):
    current_user_id = current_user_info.get("id") or routine_data.created_by_id
    
    _check_for_duplicate_routine(db, routine_data)
    _validate_routine_data(db, routine_data, bearer_token=current_user_info.get("bearer_token"))
    
    db_routine = models.Routine(**routine_data.model_dump())
    db_routine.created_by_id = current_user_id
    db_routine.created_date = datetime.now()
    db.add(db_routine)
    
    try:
        db.commit()
        db.refresh(db_routine)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Routine record: {e}")
    
    updated_data_dict = serialize_data(routine_data.model_dump())
    
    log_crud_action(
        action=ActionType.CREATE,
        user=current_user_id,
        user_full_name=current_user_info.get("fullname"),
        message="Created Routine record",
        table="ROUTINE",
        entity_id=db_routine.id,
        original_data=None,
        updated_data=updated_data_dict
    )
    
    return db_routine

def get_routine_by_id(
    db: Session,
    routine_id: int,
    include_deleted: bool = False
):
    if include_deleted:
        db_routine = db.query(models.Routine).filter(models.Routine.id == routine_id).first()
    else:
        db_routine = db.query(models.Routine).filter(models.Routine.id == routine_id, models.Routine.is_deleted == False).first()
    
    if not db_routine:
        raise HTTPException(status_code=404, detail="Routine record not found")
    
    return db_routine

def get_routines(
    db: Session,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.Routine)
    if not include_deleted:
        query = query.filter(models.Routine.is_deleted == False)
    query = query.order_by(models.Routine.start_time.asc())
    routines = query.offset(skip).limit(limit).all()
    if not routines:
        raise HTTPException(status_code=404, detail="No Routine records found")
    return routines

def get_routines_by_patient_id(
    db: Session,
    patient_id: int,
    include_deleted: bool = False
):
    query = db.query(models.Routine).filter(models.Routine.patient_id == patient_id)
    if not include_deleted:
        query = query.filter(models.Routine.is_deleted == False)
    query = query.order_by(models.Routine.day_of_week.asc(), models.Routine.start_time.asc())
    results = query.all()
    if not results:
        raise HTTPException(status_code=404, detail="No Routine records for this patient")
    return results

def update_routine(
    db: Session,
    routine_data: schemas.RoutineUpdate,
    current_user_info: dict
):
    db_routine = db.query(models.Routine).filter(models.Routine.id == routine_data.id).first()
    
    if not db_routine:
        raise HTTPException(status_code=404, detail="Routine record not found")
    
    _check_for_duplicate_routine(db, routine_data, exclude_id=routine_data.id)
    _validate_routine_data(db, routine_data, bearer_token=current_user_info.get("bearer_token"))
    
    original_data_dict = serialize_data(model_to_dict(db_routine))
    
    db_routine.activity_id = routine_data.activity_id
    db_routine.patient_id = routine_data.patient_id
    db_routine.day_of_week = routine_data.day_of_week
    db_routine.start_time = routine_data.start_time
    db_routine.end_time = routine_data.end_time
    db_routine.start_date = routine_data.start_date
    db_routine.end_date = routine_data.end_date
    db_routine.is_deleted = routine_data.is_deleted
    db_routine.modified_by_id = routine_data.modified_by_id
    db_routine.modified_date = routine_data.modified_date or datetime.now()
    
    try:
        db.commit()
        db.refresh(db_routine)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Routine record: {e}")
    
    updated_data_dict = serialize_data(model_to_dict(db_routine))
    
    log_crud_action(
        action=ActionType.UPDATE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Updated Routine record",
        table="ROUTINE",
        entity_id=db_routine.id,
        original_data=original_data_dict,
        updated_data=updated_data_dict
    )
    
    return db_routine

def delete_routine(
    db: Session,
    routine_id: int,
    current_user_info: dict
):
    db_routine = db.query(models.Routine).filter(models.Routine.id == routine_id).first()
    
    if not db_routine:
        raise HTTPException(status_code=404, detail="Routine record not found")
    
    original_data_dict = serialize_data(model_to_dict(db_routine))
    
    db_routine.is_deleted = True
    db_routine.modified_by_id = current_user_info.get("id")
    db_routine.modified_date = datetime.now()
    
    try:
        db.commit()
        db.refresh(db_routine)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Routine record: {e}")
    
    log_crud_action(
        action=ActionType.DELETE,
        user=current_user_info.get("id"),
        user_full_name=current_user_info.get("fullname"),
        message="Deleted Routine record",
        table="ROUTINE",
        entity_id=db_routine.id,
        original_data=original_data_dict,
        updated_data=None
    )
    
    return db_routine

import logging
from typing import Any, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
import app.models.routine_model as models
import app.schemas.routine_schema as schemas
from app.crud.activity_crud import get_activity_by_id
from app.services.patient_service import get_patient_by_id, get_patient_name
from app.services.outbox_service import get_outbox_service, generate_correlation_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict

logger = logging.getLogger(__name__)


def _routine_to_dict(routine, activity_title: str = None) -> Dict[str, Any]:
    """Convert a Routine model into a JSON-serialisable dict for messaging."""
    data = {}
    for key, value in routine.__dict__.items():
        if key.startswith("_"):
            continue
        data[key] = value.isoformat() if hasattr(value, "isoformat") else value
    if activity_title is not None:
        data["activity_title"] = activity_title
    return data


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
    current_user_info: dict,
    correlation_id: str = None
):
    current_user_id = current_user_info.get("id")

    _check_for_duplicate_routine(db, routine_data)
    _validate_routine_data(db, routine_data, bearer_token=current_user_info.get("bearer_token"))

    if not correlation_id:
        correlation_id = generate_correlation_id()

    activity = get_activity_by_id(db, activity_id=routine_data.activity_id)
    activity_name = activity.title if activity else "Unknown"

    try:
        timestamp = datetime.now()
        db_routine = models.Routine(**routine_data.model_dump())
        db_routine.created_by_id = current_user_id
        db_routine.created_date = timestamp
        db.add(db_routine)
        db.flush()  # assign the primary key without committing

        # Emit the domain event in the same transaction (outbox pattern)
        event_payload = {
            "event_type": "ROUTINE_CREATED",
            "routine_id": db_routine.id,
            "routine_data": _routine_to_dict(db_routine, activity_name),
            "created_by": current_user_id,
            "created_by_name": current_user_info.get("fullname"),
            "timestamp": timestamp.isoformat(),
            "correlation_id": correlation_id,
        }
        outbox_event = get_outbox_service().create_event(
            db=db,
            event_type="ROUTINE_CREATED",
            aggregate_id=db_routine.id,
            payload=event_payload,
            routing_key=f"routine.created.{db_routine.id}",
            correlation_id=correlation_id,
            created_by=current_user_id,
        )

        patient_name = get_patient_name(routine_data.patient_id, current_user_info.get("bearer_token"))
        log_crud_action(
            action=ActionType.CREATE,
            user=current_user_id,
            user_full_name=current_user_info.get("fullname"),
            message=f"Created Routine: {routine_data.name} ({activity_name}) for {patient_name}",
            table="ROUTINE",
            entity_id=db_routine.id,
            original_data=None,
            updated_data=serialize_data(routine_data.model_dump()),
            patient_id=routine_data.patient_id,
            patient_full_name=patient_name,
            log_type = "activity",
            is_system_config = False,
        )

        db.commit()
        db.refresh(db_routine)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create routine: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating Routine record: {e}")

    logger.info(
        f"Created routine {db_routine.id} with outbox event {outbox_event.id} "
        f"(correlation: {correlation_id})"
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
    current_user_info: dict,
    correlation_id: str = None
):
    db_routine = db.query(models.Routine).filter(models.Routine.id == routine_data.id).first()

    if not db_routine:
        raise HTTPException(status_code=404, detail="Routine record not found")

    _check_for_duplicate_routine(db, routine_data, exclude_id=routine_data.id)
    _validate_routine_data(db, routine_data, bearer_token=current_user_info.get("bearer_token"))

    if not correlation_id:
        correlation_id = generate_correlation_id()

    activity = get_activity_by_id(db, activity_id=routine_data.activity_id)
    activity_name = activity.title if activity else "Unknown"

    original_data_dict = serialize_data(model_to_dict(db_routine))
    old_routine_dict = _routine_to_dict(db_routine, activity_name)

    new_values = {
        "name": routine_data.name,
        "activity_id": routine_data.activity_id,
        "patient_id": routine_data.patient_id,
        "day_of_week": routine_data.day_of_week,
        "start_time": routine_data.start_time,
        "end_time": routine_data.end_time,
        "start_date": routine_data.start_date,
        "end_date": routine_data.end_date,
    }
    changes = {
        field: {"old": serialize_data(getattr(db_routine, field)), "new": serialize_data(new_value)}
        for field, new_value in new_values.items()
        if getattr(db_routine, field) != new_value
    }

    try:
        timestamp = datetime.now()
        for field, new_value in new_values.items():
            setattr(db_routine, field, new_value)
        db_routine.modified_by_id = current_user_info.get("id")
        db_routine.modified_date = timestamp
        db.flush()

        event_payload = {
            "event_type": "ROUTINE_UPDATED",
            "routine_id": db_routine.id,
            "old_data": old_routine_dict,
            "new_data": _routine_to_dict(db_routine, activity_name),
            "changes": changes,
            "modified_by": current_user_info.get("id"),
            "modified_by_name": current_user_info.get("fullname"),
            "timestamp": timestamp.isoformat(),
            "correlation_id": correlation_id,
        }
        outbox_event = get_outbox_service().create_event(
            db=db,
            event_type="ROUTINE_UPDATED",
            aggregate_id=db_routine.id,
            payload=event_payload,
            routing_key=f"routine.updated.{db_routine.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id"),
        )

        patient_name = get_patient_name(routine_data.patient_id, current_user_info.get("bearer_token", ""))
        log_crud_action(
            action=ActionType.UPDATE,
            user=current_user_info.get("id"),
            user_full_name=current_user_info.get("fullname"),
            message=f"Updated Routine: {routine_data.name} ({activity_name}) for {patient_name}",
            table="ROUTINE",
            entity_id=db_routine.id,
            original_data=original_data_dict,
            updated_data=serialize_data(model_to_dict(db_routine)),
            patient_id=routine_data.patient_id,
            patient_full_name=patient_name,
            log_type = "activity",
            is_system_config = False,
        )

        db.commit()
        db.refresh(db_routine)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update routine {routine_data.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating Routine record: {e}")

    logger.info(
        f"Updated routine {db_routine.id} with outbox event {outbox_event.id} "
        f"(correlation: {correlation_id})"
    )
    return db_routine

def delete_routine(
    db: Session,
    routine_id: int,
    current_user_info: dict,
    correlation_id: str = None
):
    db_routine = db.query(models.Routine).filter(models.Routine.id == routine_id).first()

    if not db_routine:
        raise HTTPException(status_code=404, detail="Routine record not found")

    if not correlation_id:
        correlation_id = generate_correlation_id()

    original_data_dict = serialize_data(model_to_dict(db_routine))
    patient_name = get_patient_name(db_routine.patient_id, current_user_info.get("bearer_token", ""))
    activity = get_activity_by_id(db, activity_id=db_routine.activity_id)
    activity_name = activity.title if activity else "Unknown"

    try:
        timestamp = datetime.now()
        db_routine.is_deleted = True
        db_routine.modified_by_id = current_user_info.get("id")
        db_routine.modified_date = timestamp
        db.flush()

        event_payload = {
            "event_type": "ROUTINE_DELETED",
            "routine_id": db_routine.id,
            "routine_data": _routine_to_dict(db_routine, activity_name),
            "deleted_by": current_user_info.get("id"),
            "deleted_by_name": current_user_info.get("fullname"),
            "timestamp": timestamp.isoformat(),
            "correlation_id": correlation_id,
        }
        outbox_event = get_outbox_service().create_event(
            db=db,
            event_type="ROUTINE_DELETED",
            aggregate_id=db_routine.id,
            payload=event_payload,
            routing_key=f"routine.deleted.{db_routine.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id"),
        )

        log_crud_action(
            action=ActionType.DELETE,
            user=current_user_info.get("id"),
            user_full_name=current_user_info.get("fullname"),
            message=f"Deleted Routine: {db_routine.name} ({activity_name}) for {patient_name})",
            table="ROUTINE",
            entity_id=db_routine.id,
            original_data=original_data_dict,
            updated_data=None,
            patient_id=db_routine.patient_id,
            patient_full_name=patient_name,
            log_type = "activity",
            is_system_config = False,
        )

        db.commit()
        db.refresh(db_routine)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete routine {routine_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting Routine record: {e}")

    logger.info(
        f"Deleted routine {db_routine.id} with outbox event {outbox_event.id} "
        f"(correlation: {correlation_id})"
    )
    return db_routine

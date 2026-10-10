import logging
from sqlalchemy.orm import Session
import app.models.adhoc_model as models
import app.schemas.adhoc_schema as schemas
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.services.patient_service import get_patient_by_id
from app.services.patient_service import get_patient_name
from app.services.outbox_service import get_outbox_service, generate_correlation_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from fastapi import HTTPException
from typing import Any, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


def _centre_activity_title(centre_activity) -> str:
    """Resolve the activity title behind a CentreActivity, if available."""
    if centre_activity and centre_activity.activity:
        return centre_activity.activity.title
    return "Unknown"


def _adhoc_to_dict(
    adhoc,
    old_activity_title: str = None,
    new_activity_title: str = None
) -> Dict[str, Any]:
    """Convert an Adhoc model into a JSON-serialisable dict for messaging.

    Only mapped columns are emitted - loaded relationships (old_centre_activity,
    new_centre_activity) must never leak into the payload.
    """
    data = {}
    for column in models.Adhoc.__table__.columns.keys():
        value = getattr(adhoc, column, None)
        data[column] = value.isoformat() if hasattr(value, "isoformat") else value
    if old_activity_title is not None:
        data["old_activity_title"] = old_activity_title
    if new_activity_title is not None:
        data["new_activity_title"] = new_activity_title
    return data


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
    current_user_info: dict,
    correlation_id: str = None
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
        get_patient_by_id(
            require_auth=True,
            bearer_token=current_user_info.get("bearer_token", ""),
            patient_id=adhoc_data.patient_id,
        )
    except HTTPException as e:
        raise HTTPException(status_code=400, detail="Invalid Patient ID") from e

    if not correlation_id:
        correlation_id = generate_correlation_id()

    current_user_id = current_user_info.get("id")
    old_activity_name = _centre_activity_title(old_ca)
    new_activity_name = _centre_activity_title(new_ca)

    db_adhoc = models.Adhoc(**adhoc_data.model_dump())
    try:
        timestamp = datetime.now()
        db.add(db_adhoc)
        db.flush()  # assign the primary key without committing

        # Emit the domain event in the same transaction (outbox pattern)
        event_payload = {
            "event_type": "ADHOC_CREATED",
            "adhoc_id": db_adhoc.id,
            "adhoc_data": _adhoc_to_dict(db_adhoc, old_activity_name, new_activity_name),
            "created_by": current_user_id,
            "created_by_name": current_user_info.get("fullname"),
            "timestamp": timestamp.isoformat(),
            "correlation_id": correlation_id,
        }
        outbox_event = get_outbox_service().create_event(
            db=db,
            event_type="ADHOC_CREATED",
            aggregate_id=db_adhoc.id,
            payload=event_payload,
            routing_key=f"activity.adhoc.created.{db_adhoc.id}",
            correlation_id=correlation_id,
            created_by=current_user_id,
        )

        patient_name = get_patient_name(adhoc_data.patient_id, current_user_info.get("bearer_token", ""))
        log_crud_action(
            action=ActionType.CREATE,
            user=current_user_id,
            user_full_name=current_user_info.get("fullname"),
            message=f"Created Adhoc change: {old_activity_name} -> {new_activity_name} for patient: {patient_name}",
            table="ADHOC",
            entity_id=db_adhoc.id,
            original_data=None,
            updated_data=serialize_data(model_to_dict(db_adhoc)),
            patient_id = adhoc_data.patient_id,
            patient_full_name= patient_name,
            log_type = "activity",
            is_system_config= False
        )

        db.commit()
        db.refresh(db_adhoc)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create adhoc: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating Adhoc record: {e}")

    logger.info(
        f"Created adhoc {db_adhoc.id} with outbox event {outbox_event.id} "
        f"(correlation: {correlation_id})"
    )
    return db_adhoc

def update_adhoc(
    db: Session,
    adhoc_data: schemas.AdhocUpdate,
    current_user_info: dict,
    correlation_id: str = None
) -> models.Adhoc:
    db_adhoc = db.query(models.Adhoc).filter(models.Adhoc.id == adhoc_data.id).first()
    if not db_adhoc:
        raise HTTPException(status_code=404, detail="Adhoc record not found")

    original = serialize_data(model_to_dict(db_adhoc))

    old_ca = None
    new_ca = None
    if adhoc_data.old_centre_activity_id is not None:
        old_ca = get_centre_activity_by_id(db, centre_activity_id=adhoc_data.old_centre_activity_id)
    if adhoc_data.new_centre_activity_id is not None:
        new_ca = get_centre_activity_by_id(db, centre_activity_id=adhoc_data.new_centre_activity_id)

    # validate patient
    try:
        get_patient_by_id(
            require_auth=True,
            bearer_token=current_user_info.get("bearer_token", ""),
            patient_id=adhoc_data.patient_id,
        )
    except HTTPException as e:
        raise HTTPException(status_code=400, detail="Invalid Patient ID") from e

    if not correlation_id:
        correlation_id = generate_correlation_id()

    current_user_id = current_user_info.get("id")
    old_activity_name = _centre_activity_title(old_ca)
    new_activity_name = _centre_activity_title(new_ca)
    old_adhoc_dict = _adhoc_to_dict(db_adhoc)

    new_values = {
        "old_centre_activity_id": adhoc_data.old_centre_activity_id,
        "new_centre_activity_id": adhoc_data.new_centre_activity_id,
        "patient_id": adhoc_data.patient_id,
        "status": adhoc_data.status,
        "start_date": adhoc_data.start_date,
        "end_date": adhoc_data.end_date,
        "is_deleted": adhoc_data.is_deleted,
    }
    changes = {
        field: {"old": serialize_data(getattr(db_adhoc, field)), "new": serialize_data(new_value)}
        for field, new_value in new_values.items()
        if getattr(db_adhoc, field) != new_value
    }

    try:
        for field, new_value in new_values.items():
            setattr(db_adhoc, field, new_value)
        # stamp modification
        db_adhoc.modified_date = adhoc_data.modified_date or datetime.now()
        db_adhoc.modified_by_id = adhoc_data.modified_by_id
        db.flush()

        event_payload = {
            "event_type": "ADHOC_UPDATED",
            "adhoc_id": db_adhoc.id,
            "adhoc_data": _adhoc_to_dict(db_adhoc, old_activity_name, new_activity_name),
            "old_data": old_adhoc_dict,
            "changes": changes,
            "modified_by": current_user_id,
            "modified_by_name": current_user_info.get("fullname"),
            "timestamp": db_adhoc.modified_date.isoformat(),
            "correlation_id": correlation_id,
        }
        outbox_event = get_outbox_service().create_event(
            db=db,
            event_type="ADHOC_UPDATED",
            aggregate_id=db_adhoc.id,
            payload=event_payload,
            routing_key=f"activity.adhoc.updated.{db_adhoc.id}",
            correlation_id=correlation_id,
            created_by=current_user_id,
        )

        updated = serialize_data(model_to_dict(db_adhoc))
        patient_name = get_patient_name(adhoc_data.patient_id, current_user_info.get("bearer_token", ""))
        log_crud_action(
            action=ActionType.UPDATE,
            user=current_user_id,
            user_full_name=current_user_info.get("fullname"),
            message=f"Updated Adhoc change: {old_activity_name} -> {new_activity_name} for patient: {patient_name}",
            table="ADHOC",
            entity_id=db_adhoc.id,
            original_data=original,
            updated_data=updated,
            patient_id = adhoc_data.patient_id,
            patient_full_name= patient_name,
            log_type = "activity",
            is_system_config= False,
        )

        db.commit()
        db.refresh(db_adhoc)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update adhoc {adhoc_data.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating Adhoc record: {e}")

    logger.info(
        f"Updated adhoc {db_adhoc.id} with outbox event {outbox_event.id} "
        f"(correlation: {correlation_id})"
    )
    return db_adhoc

def delete_adhoc(
    db: Session,
    adhoc_id: int,
    current_user_info: dict,
    correlation_id: str = None
) -> models.Adhoc:
    db_adhoc = db.query(models.Adhoc).filter(models.Adhoc.id == adhoc_id).first()
    if not db_adhoc:
        raise HTTPException(status_code=404, detail="Adhoc record not found")

    if not correlation_id:
        correlation_id = generate_correlation_id()

    current_user_id = current_user_info.get("id")
    original = serialize_data(model_to_dict(db_adhoc))
    old_activity_name = _centre_activity_title(db_adhoc.old_centre_activity)
    new_activity_name = _centre_activity_title(db_adhoc.new_centre_activity)

    try:
        timestamp = datetime.now()
        db_adhoc.is_deleted = True
        db_adhoc.modified_date = timestamp
        db_adhoc.modified_by_id = current_user_id
        db.flush()

        event_payload = {
            "event_type": "ADHOC_DELETED",
            "adhoc_id": db_adhoc.id,
            "adhoc_data": _adhoc_to_dict(db_adhoc, old_activity_name, new_activity_name),
            "deleted_by": current_user_id,
            "deleted_by_name": current_user_info.get("fullname"),
            "timestamp": timestamp.isoformat(),
            "correlation_id": correlation_id,
        }
        outbox_event = get_outbox_service().create_event(
            db=db,
            event_type="ADHOC_DELETED",
            aggregate_id=db_adhoc.id,
            payload=event_payload,
            routing_key=f"activity.adhoc.deleted.{db_adhoc.id}",
            correlation_id=correlation_id,
            created_by=current_user_id,
        )

        patient_name = get_patient_name(db_adhoc.patient_id, current_user_info.get("bearer_token", ""))
        log_crud_action(
            action=ActionType.DELETE,
            user=current_user_id,
            user_full_name=current_user_info.get("fullname"),
            message=f"Deleted Adhoc change: {old_activity_name} -> {new_activity_name} for patient: {patient_name}",
            table="ADHOC",
            entity_id=db_adhoc.id,
            original_data=original,
            updated_data=None,
            patient_id = db_adhoc.patient_id,
            patient_full_name= patient_name,
            log_type = "activity",
            is_system_config= False,
        )

        db.commit()
        db.refresh(db_adhoc)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete adhoc {adhoc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting Adhoc record: {e}")

    logger.info(
        f"Deleted adhoc {db_adhoc.id} with outbox event {outbox_event.id} "
        f"(correlation: {correlation_id})"
    )
    return db_adhoc
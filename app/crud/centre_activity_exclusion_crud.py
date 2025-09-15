import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.models.centre_activity_exclusion_model as models
import app.schemas.centre_activity_exclusion_schema as schemas
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.logger.logger_utils import (
    ActionType,
    log_crud_action,
    model_to_dict,
    serialize_data,
)
from app.services.patient_service import get_patient_by_id

from ..services.outbox_service import generate_correlation_id, get_outbox_service

logger = logging.getLogger(__name__)

# def _centre_activity_exclusion_to_dict(activity) -> Dict[str, Any]:
#     """Convert centre activity model to dictionary for messaging"""
#     try:
#         if hasattr(activity, '__dict__'):
#             activity_dict = {}
#             for key, value in activity.__dict__.items():
#                 if not key.startswith('_'):
#                     # Convert datetime objects to ISO format strings
#                     if hasattr(value, 'isoformat'):
#                         activity_dict[key] = value.isoformat()
#                     else:
#                         activity_dict[key] = value
#             return activity_dict
#         else:
#             return {}
#     except Exception as e:
#         logger.error(f"Error converting activity to dict: {str(e)}")
#         return {}

def get_centre_activity_exclusion_by_id(
    db: Session,
    exclusion_id: int,
    include_deleted: bool = False
) -> models.CentreActivityExclusion:
    q = db.query(models.CentreActivityExclusion).filter(models.CentreActivityExclusion.id == exclusion_id)
    if not include_deleted:
        q = q.filter(models.CentreActivityExclusion.is_deleted == False)
    obj = q.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Centre Activity Exclusion not found")
    return obj

def get_centre_activity_exclusions(
    db: Session,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[models.CentreActivityExclusion]:
    q = db.query(models.CentreActivityExclusion)
    if not include_deleted:
        q = q.filter(models.CentreActivityExclusion.is_deleted == False)
    return (
        q.order_by(models.CentreActivityExclusion.id)
         .offset(skip)
         .limit(limit)
         .all()
    )

def create_centre_activity_exclusion(
    db: Session,
    exclusion_data: schemas.CentreActivityExclusionCreate,
    current_user_info: dict,
    correlation_id: str = None
) -> models.CentreActivityExclusion:
    # 1) Validate centre activity exists
    if not get_centre_activity_by_id(db, centre_activity_id=exclusion_data.centre_activity_id):
        raise HTTPException(status_code=404, detail="Centre Activity not found")

    # 2) Validate patient exists (via external service)
    try:
        get_patient_by_id(
            require_auth=True,
            bearer_token=current_user_info.get("bearer_token", ""),
            patient_id=exclusion_data.patient_id,
        )
    except HTTPException:
        raise HTTPException(status_code=400, detail="Invalid Patient ID")

    obj = models.CentreActivityExclusion(**exclusion_data.model_dump())
    obj.created_by_id  = current_user_info["id"]
    obj.modified_by_id = current_user_info["id"]
    db.add(obj)
    db.flush()  # Get the ID without committing
    print("Object in dict form: ", serialize_data(model_to_dict(obj)))
    try:
        
        # Create outbox event in the same transaction
        outbox_service = get_outbox_service()
        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = generate_correlation_id()
            
        event_payload = {
            'event_type': 'CENTRE_ACTIVITY_EXCLUSION_CREATED',
            'centre_activity_id': obj.id,
            'patient_id': obj.patient_id,
            'centre_activity_data': serialize_data(model_to_dict(obj)),
            'created_by': obj.created_by_id,
            'created_by_name': current_user_info.get("fullname"),
            'modified_by': obj.modified_by_id,
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='CENTRE_ACTIVITY_EXCLUSION_CREATED',
            aggregate_id=obj.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity_exclusion.created.{obj.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id")
        )
        
        db.commit()
        db.refresh(obj)
        logger.info(f"Created centre activity exclusion {obj.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating exclusion: {e}")

    log_crud_action(
        action=ActionType.CREATE,
        user=current_user_info["id"],
        user_full_name=current_user_info.get("fullname"),
        message="Created Centre Activity Exclusion",
        table="CENTRE_ACTIVITY_EXCLUSION",
        entity_id=obj.id,
        original_data=None,
        updated_data=serialize_data(model_to_dict(obj))
    )
    return obj

def update_centre_activity_exclusion(
    db: Session,
    exclusion_data: schemas.CentreActivityExclusionUpdate,
    current_user_info: dict,
    correlation_id: str = None
) -> models.CentreActivityExclusion:
    db_obj = get_centre_activity_exclusion_by_id(db, exclusion_data.id, include_deleted=True)
    original = serialize_data(model_to_dict(db_obj))

    if exclusion_data.centre_activity_id is not None:
        if not get_centre_activity_by_id(db, centre_activity_id=exclusion_data.centre_activity_id):
            raise HTTPException(status_code=404, detail="Centre Activity not found")
        db_obj.centre_activity_id = exclusion_data.centre_activity_id

    if exclusion_data.patient_id is not None:
        try:
            get_patient_by_id(
                require_auth=True,
                bearer_token=current_user_info.get("bearer_token", ""),
                patient_id=exclusion_data.patient_id,
            )
        except HTTPException:
            raise HTTPException(status_code=400, detail="Invalid Patient ID")
        db_obj.patient_id = exclusion_data.patient_id

    # update all other fields if provided
    update_data = exclusion_data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_obj, k, v)
    db.flush()
    
    try:
        # Create outbox event in the same transaction
        outbox_service = get_outbox_service()
        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = generate_correlation_id()
            
        event_payload = {
            'event_type': 'CENTRE_ACTIVITY_EXCLUSION_UPDATED',
            'centre_activity_id': db_obj.id,
            'original_centre_activity_data': original,
            'new_centre_activity_data': serialize_data(model_to_dict(db_obj)),
            'modified_by': db_obj.modified_by_id,
            'modified_by_name': current_user_info.get("fullname"),
            'modified_date': db_obj.modified_date.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='CENTRE_ACTIVITY_EXCLUSION_UPDATED',
            aggregate_id=db_obj.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity_exclusion.updated.{db_obj.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id")
        )
        
        db.commit()
        db.refresh(db_obj)
        logger.info(f"Updated centre activity exclusion {db_obj.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating exclusion: {e}")

    log_crud_action(
        action=ActionType.UPDATE,
        user=current_user_info["id"],
        user_full_name=current_user_info.get("fullname"),
        message="Updated Centre Activity Exclusion",
        table="CENTRE_ACTIVITY_EXCLUSION",
        entity_id=db_obj.id,
        original_data=original,
        updated_data=serialize_data(model_to_dict(db_obj))
    )
    return db_obj

def delete_centre_activity_exclusion(
    db: Session,
    exclusion_id: int,
    current_user_info: dict,
    correlation_id: str = None
) -> models.CentreActivityExclusion:
    obj = get_centre_activity_exclusion_by_id(db, exclusion_id)
    original = serialize_data(model_to_dict(obj))
    obj.is_deleted = True
    obj.modified_by_id = current_user_info["id"]
    db.flush()
    
    try:
        
        # Create outbox event in the same transaction
        outbox_service = get_outbox_service()
        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = generate_correlation_id()
            
        event_payload = {
            'event_type': 'CENTRE_ACTIVITY_EXCLUSION_DELETED',
            'centre_activity_id': obj.id,
            'centre_activity_data': original,
            'modified_by': obj.modified_by_id,
            'modified_date' : obj.modified_date.isoformat(),
            'modified_by_name': current_user_info.get("fullname"),
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='CENTRE_ACTIVITY_EXCLUSION_DELETED',
            aggregate_id=obj.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity_exclusion.deleted.{obj.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id")
        )
        logger.info(f"Deleted centre activity exclusion {obj.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")

        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting exclusion: {e}")

    log_crud_action(
        action=ActionType.DELETE,
        user=current_user_info["id"],
        user_full_name=current_user_info.get("fullname"),
        message="Deleted Centre Activity Exclusion",
        table="CENTRE_ACTIVITY_EXCLUSION",
        entity_id=obj.id,
        original_data=original,
        updated_data=None
    )
    return obj
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import app.models.centre_activity_exclusion_model as models
import app.schemas.centre_activity_exclusion_schema as schemas
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.services.patient_service import get_patient_by_id
from app.logger.logger_utils import (
    log_crud_action, ActionType, serialize_data, model_to_dict
)
from ..services.outbox_service import get_outbox_service, generate_correlation_id
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def _exclusion_to_dict(exclusion) -> Dict[str, Any]:
    """Convert centre activity exclusion model to dictionary for messaging"""
    try:
        if hasattr(exclusion, '__dict__'):
            exclusion_dict = {}
            for key, value in exclusion.__dict__.items():
                if not key.startswith('_'):
                    # Convert datetime objects to ISO format strings
                    if hasattr(value, 'isoformat'):
                        exclusion_dict[key] = value.isoformat()
                    else:
                        exclusion_dict[key] = value
            return exclusion_dict
        else:
            return {}
    except Exception as e:
        logger.error(f"Error converting exclusion to dict: {str(e)}")
        return {}

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

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Create Centre Activity Exclusion
        timestamp = datetime.now()
        current_user_id = current_user_info.get("id")
        
        obj = models.CentreActivityExclusion(**exclusion_data.model_dump())
        obj.created_by_id = current_user_id
        obj.modified_by_id = current_user_id
        obj.created_date = timestamp
        obj.modified_date = timestamp
        
        db.add(obj)
        db.flush()  # Get the ID without committing

        # 2. Create outbox event in the same transaction
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_EXCLUSION_CREATED',
            'exclusion_id': obj.id,
            'exclusion_data': _exclusion_to_dict(obj),
            'created_by': current_user_id,
            'created_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_EXCLUSION_CREATED',
            aggregate_id=obj.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity_exclusion.created.{obj.id}",
            correlation_id=correlation_id,
            created_by=current_user_id
        )

        # 3. Log the action
        log_crud_action(
            action=ActionType.CREATE,
            user=current_user_id,
            user_full_name=current_user_info.get("fullname"),
            message="Created Centre Activity Exclusion",
            table="CENTRE_ACTIVITY_EXCLUSION",
            entity_id=obj.id,
            original_data=None,
            updated_data=serialize_data(model_to_dict(obj))
        )

        # 4. Commit both exclusion and outbox event atomically
        db.commit()
        db.refresh(obj)
        
        logger.info(f"Created exclusion {obj.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return obj

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create centre activity exclusion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")

def update_centre_activity_exclusion(
    db: Session,
    exclusion_data: schemas.CentreActivityExclusionUpdate,
    current_user_info: dict,
    correlation_id: str = None
) -> models.CentreActivityExclusion:
    db_obj = get_centre_activity_exclusion_by_id(db, exclusion_data.id, include_deleted=True)

    if exclusion_data.centre_activity_id is not None:
        if not get_centre_activity_by_id(db, centre_activity_id=exclusion_data.centre_activity_id):
            raise HTTPException(status_code=404, detail="Centre Activity not found")

    if exclusion_data.patient_id is not None:
        try:
            get_patient_by_id(
                require_auth=True,
                bearer_token=current_user_info.get("bearer_token", ""),
                patient_id=exclusion_data.patient_id,
            )
        except HTTPException:
            raise HTTPException(status_code=400, detail="Invalid Patient ID")

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        original_exclusion_dict = _exclusion_to_dict(db_obj)
        original_data_dict = serialize_data(model_to_dict(db_obj))

        # 2. Track changes
        changes = {}
        update_data = exclusion_data.model_dump(exclude={'id'}, exclude_unset=True)

        # Track what actually changed, ignore audit fields
        audit_fields = {'created_by_id', 'modified_by_id', 'created_date', 'modified_date'}
        for field, new_value in update_data.items():
            if field not in audit_fields and hasattr(db_obj, field):
                old_value = getattr(db_obj, field)
                if old_value != new_value:
                    changes[field] = {
                        'old': serialize_data(old_value),
                        'new': serialize_data(new_value)
                    }

        # 3. Only proceed with update if there are actual changes
        if changes:
            # Create consistent timestamp for all audit fields
            timestamp = datetime.now()
            modified_by_id = current_user_info.get("id")

            # Add audit fields to update_data
            update_data["modified_by_id"] = modified_by_id
            update_data["modified_date"] = timestamp

            # Apply all updates
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            db.flush()

            # 4. Create outbox event only if there were changes
            outbox_service = get_outbox_service()
            
            event_payload = {
                'event_type': 'ACTIVITY_EXCLUSION_UPDATED',
                'exclusion_id': db_obj.id,
                'old_data': original_exclusion_dict,
                'new_data': _exclusion_to_dict(db_obj),
                'changes': changes,  # Only includes business field changes
                'modified_by': modified_by_id,
                'modified_by_name': current_user_info.get("fullname"),
                'timestamp': timestamp.isoformat(),
                'correlation_id': correlation_id
            }
            
            outbox_event = outbox_service.create_event(
                db=db,
                event_type='ACTIVITY_EXCLUSION_UPDATED',
                aggregate_id=db_obj.id,
                payload=event_payload,
                routing_key=f"activity.centre_activity_exclusion.updated.{db_obj.id}",
                correlation_id=correlation_id,
                created_by=modified_by_id
            )

            # 5. Log the action
            updated_data_dict = serialize_data(exclusion_data.model_dump())
            log_crud_action(
                action=ActionType.UPDATE,
                user=modified_by_id,
                user_full_name=current_user_info.get("fullname"),
                message="Updated Centre Activity Exclusion",
                table="CENTRE_ACTIVITY_EXCLUSION",
                entity_id=db_obj.id,
                original_data=original_data_dict,
                updated_data=updated_data_dict
            )

            # 6. Commit atomically
            db.commit()
            db.refresh(db_obj)
            
            logger.info(f"Updated exclusion {db_obj.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        else:
            logger.info(f"Updated exclusion {db_obj.id} with no changes")

        return db_obj

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update centre activity exclusion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")

def delete_centre_activity_exclusion(
    db: Session,
    exclusion_id: int,
    current_user_info: dict,
    correlation_id: str = None
) -> models.CentreActivityExclusion:
    obj = get_centre_activity_exclusion_by_id(db, exclusion_id)

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        exclusion_dict = _exclusion_to_dict(obj)

        # 2. Perform soft delete
        timestamp = datetime.now()
        
        obj.is_deleted = True
        obj.modified_by_id = current_user_info.get("id")
        obj.modified_date = timestamp
        
        db.flush()

        # 3. Create outbox event
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_EXCLUSION_DELETED',
            'exclusion_id': obj.id,
            'exclusion_data': exclusion_dict,
            'deleted_by': current_user_info.get("id"),
            'deleted_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_EXCLUSION_DELETED',
            aggregate_id=obj.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity_exclusion.deleted.{obj.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id")
        )

        # 4. Log the action
        original = serialize_data(model_to_dict(obj))
        log_crud_action(
            action=ActionType.DELETE,
            user=current_user_info.get("id"),
            user_full_name=current_user_info.get("fullname"),
            message="Deleted Centre Activity Exclusion",
            table="CENTRE_ACTIVITY_EXCLUSION",
            entity_id=obj.id,
            original_data=original,
            updated_data=None
        )

        # 5. Commit atomically
        db.commit()
        db.refresh(obj)
        
        logger.info(f"Deleted exclusion {obj.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return obj

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete centre activity exclusion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")

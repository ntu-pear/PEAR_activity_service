from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from ..services.outbox_service import get_outbox_service, generate_correlation_id

import app.models.activity_model as models
import app.schemas.activity_schema as schemas

logger = logging.getLogger(__name__)


def _activity_to_dict(activity) -> Dict[str, Any]:
    """Convert activity model to dictionary for messaging"""
    try:
        if hasattr(activity, '__dict__'):
            activity_dict = {}
            for key, value in activity.__dict__.items():
                if not key.startswith('_'):
                    # Convert datetime objects to ISO format strings
                    if hasattr(value, 'isoformat'):
                        activity_dict[key] = value.isoformat()
                    else:
                        activity_dict[key] = value
            return activity_dict
        else:
            return {}
    except Exception as e:
        logger.error(f"Error converting activity to dict: {str(e)}")
        return {}


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
    current_user_info: dict,
    correlation_id: str = None
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

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Create activity object
        timestamp = datetime.now()
        
        obj = models.Activity(**activity_in.model_dump(by_alias=True))
        obj.created_by_id = current_user_info.get("id")
        obj.modified_by_id = current_user_info.get("id")
        obj.created_date = timestamp
        obj.modified_date = timestamp
        
        db.add(obj)
        db.flush()  # Get the ID without committing

        # 2. Create outbox event in the same transaction
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_CREATED',
            'activity_id': obj.id,
            'activity_data': _activity_to_dict(obj),
            'created_by': current_user_info.get("id"),
            'created_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_CREATED',
            aggregate_id=obj.id,
            payload=event_payload,
            routing_key=f"activity.created.{obj.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id")
        )

        # 3. Log the action
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

        # 4. Commit both activity and outbox event atomically
        db.commit()
        db.refresh(obj)
        
        logger.info(f"Created activity {obj.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return obj

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")


def update_activity_by_id(
    db: Session,
    *,
    activity_id: int,
    activity_in: schemas.ActivityUpdate,
    current_user_info: dict,
    correlation_id: str = None
) -> models.Activity:
    
    obj = get_activity_by_id(db, activity_id=activity_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        original_activity_dict = _activity_to_dict(obj)
        original = serialize_data(model_to_dict(obj))

        # 2. Track changes
        changes = {}
        update_data = activity_in.model_dump(by_alias=True, exclude_unset=True)

        # Track what actually changed
        for field, new_value in update_data.items():
            if hasattr(obj, field):
                old_value = getattr(obj, field)
                if old_value != new_value:
                    changes[field] = {
                        'old': serialize_data(old_value),
                        'new': serialize_data(new_value)
                    }

        # 3. Only proceed with update if there are actual changes
        if changes:
            # Create consistent timestamp for all audit fields
            timestamp = datetime.now()
            
            # Add audit fields to update_data
            update_data["modified_by_id"] = current_user_info.get("id")
            update_data["modified_date"] = timestamp

            # Apply all updates
            for field, value in update_data.items():
                setattr(obj, field, value)

            db.flush()

            # 4. Create outbox event only if there were changes
            outbox_service = get_outbox_service()
            
            event_payload = {
                'event_type': 'ACTIVITY_UPDATED',
                'activity_id': obj.id,
                'old_data': original_activity_dict,
                'new_data': _activity_to_dict(obj),
                'changes': changes,  # Only includes business field changes
                'modified_by': current_user_info.get("id"),
                'modified_by_name': current_user_info.get("fullname"),
                'timestamp': timestamp.isoformat(),  # Use same timestamp as obj.modified_date
                'correlation_id': correlation_id
            }
            
            outbox_event = outbox_service.create_event(
                db=db,
                event_type='ACTIVITY_UPDATED',
                aggregate_id=obj.id,
                payload=event_payload,
                routing_key=f"activity.updated.{obj.id}",
                correlation_id=correlation_id,
                created_by=current_user_info.get("id")
            )

            # 5. Log the action
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

            # 6. Commit atomically
            db.commit()
            db.refresh(obj)
            
            logger.info(f"Updated activity {obj.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        else:
            logger.info(f"Updated activity {obj.id} with no changes")

        return obj

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")


def delete_activity_by_id(
    db: Session,
    *,
    activity_id: int,
    current_user_info: dict,
    correlation_id: str = None
) -> models.Activity:
    
    obj = get_activity_by_id(db, activity_id=activity_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or already deleted"
        )

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        original = serialize_data(model_to_dict(obj))

        # 2. Perform soft delete
        timestamp = datetime.now()
        
        obj.is_deleted = True
        obj.modified_by_id = current_user_info.get("id")
        obj.modified_date = timestamp
        
        db.flush()
        
        # 3. Capture activity data AFTER soft delete to include updated modified_date
        activity_dict = _activity_to_dict(obj)

        # 4. Create outbox event
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_DELETED',
            'activity_id': obj.id,
            'activity_data': activity_dict,
            'deleted_by': current_user_info.get("id"),
            'deleted_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_DELETED',
            aggregate_id=obj.id,
            payload=event_payload,
            routing_key=f"activity.deleted.{obj.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id")
        )

        # 5. Log the action
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

        # 6. Commit atomically
        db.commit()
        db.refresh(obj)
        
        logger.info(f"Deleted activity {obj.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return obj

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")

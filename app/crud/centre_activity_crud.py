from typing import Dict, Any
from sqlalchemy.orm import Session
import app.models.centre_activity_model as models
import app.schemas.centre_activity_schema as schemas
from app.crud.activity_crud import get_activity_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from ..services.outbox_service import get_outbox_service, generate_correlation_id
from fastapi import HTTPException
from typing import List, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Helper validation functions
def _validate_activity_exists(db: Session, activity_id: int):
    """Validate that activity exists"""
    activity = get_activity_by_id(db, activity_id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

def _validate_and_detect_changes(
    db: Session,
    centre_activity_data: Union[schemas.CentreActivityCreate, schemas.CentreActivityUpdate],
    db_centre_activity = None,
    exclude_id: int = None
):
    """
    Universal function for duplicate validation and change detection.
    - For CREATE: Only validates duplicates (db_centre_activity=None)
    - For UPDATE: Validates duplicates AND detects changes (db_centre_activity provided)
    Returns changes dict for updates, None for creates, raises HTTPException if duplicate.
    """
    # Define essential business fields
    essential_fields = {
        "activity_id", "is_compulsory", "is_fixed", "is_group",
        "start_date", "end_date", "min_duration", "max_duration", "min_people_req"
    }
    
    # For CREATE operations - just check duplicates
    if db_centre_activity is None:
        query_fields = {
            "activity_id": centre_activity_data.activity_id,
            "is_compulsory": centre_activity_data.is_compulsory,
            "is_fixed": centre_activity_data.is_fixed,
            "is_group": centre_activity_data.is_group,
            "start_date": centre_activity_data.start_date,
            "end_date": centre_activity_data.end_date,
            "min_duration": centre_activity_data.min_duration,
            "max_duration": centre_activity_data.max_duration,
            "min_people_req": centre_activity_data.min_people_req,
        }
        
        query = db.query(models.CentreActivity).filter_by(**query_fields)
        
        if exclude_id is not None:
            query = query.filter(models.CentreActivity.id != exclude_id)
        
        existing_centre_activity = query.first()
        
        if existing_centre_activity:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Centre Activity with these attributes already exists or deleted",
                    "existing_id": str(existing_centre_activity.id),
                    "existing_is_deleted": existing_centre_activity.is_deleted
                }
            )
        return None  # No changes to return for create
    
    # For UPDATE operations - detect changes AND validate duplicates
    audit_fields = {'created_by_id', 'modified_by_id', 'created_date', 'modified_date'}
    update_data = centre_activity_data.model_dump(exclude={'id'}, exclude_unset=True)
    changes = {}
    essential_field_changes = {}
    
    # Single pass: detect all changes
    for field, new_value in update_data.items():
        if field not in audit_fields and hasattr(db_centre_activity, field):
            old_value = getattr(db_centre_activity, field)
            if old_value != new_value:
                changes[field] = {
                    'old': serialize_data(old_value),
                    'new': serialize_data(new_value)
                }
                # Track essential field changes for duplicate checking
                if field in essential_fields:
                    essential_field_changes[field] = new_value
    
    # If no changes at all, return early
    if not changes:
        return None  # Indicates no changes detected
    
    # If there are essential field changes, check for duplicates
    if essential_field_changes:
        # Build query with current + changed essential fields
        query_fields = {}
        for field in essential_fields:
            if field in essential_field_changes:
                query_fields[field] = essential_field_changes[field]
            else:
                query_fields[field] = getattr(db_centre_activity, field)
        
        query = db.query(models.CentreActivity).filter_by(**query_fields)
        
        if exclude_id is not None:
            query = query.filter(models.CentreActivity.id != exclude_id)
        
        existing_centre_activity = query.first()
        
        if existing_centre_activity:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Centre Activity with these attributes already exists or deleted",
                    "existing_id": str(existing_centre_activity.id),
                    "existing_is_deleted": existing_centre_activity.is_deleted
                }
            )
    
    return changes

def _centre_activity_to_dict(centre_activity) -> Dict[str, Any]:
    """Convert centre activity model to dictionary for messaging"""
    try:
        if hasattr(centre_activity, '__dict__'):
            activity_dict = {}
            for key, value in centre_activity.__dict__.items():
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
        logger.error(f"Error converting centre activity to dict: {str(e)}")
        return {}

def create_centre_activity(
        db: Session, 
        centre_activity_data: schemas.CentreActivityCreate, 
        current_user_info: dict,
        correlation_id: str = None
        ):
    
    # Validate dependencies and check for duplicates
    _validate_activity_exists(db, centre_activity_data.activity_id)
    _validate_and_detect_changes(db, centre_activity_data)
    
    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()
    
    try:
        # 1. Create Centre Activity
        timestamp = datetime.utcnow()
        current_user_id = current_user_info.get("id") or centre_activity_data.created_by_id
        
        db_centre_activity = models.CentreActivity(**centre_activity_data.model_dump())
        db_centre_activity.created_by_id = current_user_id
        db_centre_activity.modified_by_id = current_user_id
        db_centre_activity.created_date = timestamp
        db_centre_activity.modified_date = timestamp
        
        db.add(db_centre_activity)
        db.flush()  # Get the ID without committing
        
        # 2. Create outbox event in the same transaction
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'CENTRE_ACTIVITY_CREATED',
            'centre_activity_id': db_centre_activity.id,
            'centre_activity_data': _centre_activity_to_dict(db_centre_activity),
            'created_by': current_user_id,
            'created_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='CENTRE_ACTIVITY_CREATED',
            aggregate_id=db_centre_activity.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity.created.{db_centre_activity.id}",
            correlation_id=correlation_id,
            created_by=current_user_id
        )

        # 3. Log the action
        updated_data_dict = serialize_data(centre_activity_data.model_dump())
        log_crud_action(
            action=ActionType.CREATE,
            user=current_user_id,
            user_full_name=current_user_info.get("fullname"),
            message="Created a new Centre Activity",
            table="CENTRE_ACTIVITY",
            entity_id=db_centre_activity.id,
            original_data=None,
            updated_data=updated_data_dict
        )

        # 4. Commit both centre activity and outbox event atomically
        db.commit()
        db.refresh(db_centre_activity)
        
        logger.info(f"Created centre activity {db_centre_activity.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return db_centre_activity

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create centre activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating Centre Activity: {str(e)}")


def get_centre_activity_by_id(
        db: Session, 
        centre_activity_id: int,
        include_deleted: bool = False
        ):
    db_centre_activity = db.query(models.CentreActivity)

    if not include_deleted:
        db_centre_activity = db_centre_activity.filter(models.CentreActivity.is_deleted == False)

    db_centre_activity = db_centre_activity.filter(
        models.CentreActivity.id == centre_activity_id
    ).first()
    
    if not db_centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found")
    return db_centre_activity


def get_centre_activities(
        db: Session,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
    ):
    db_centre_activities = db.query(models.CentreActivity)

    # Exclude is_deleted=True records, else show all records if include_deleted is True
    if not include_deleted:
        db_centre_activities = db_centre_activities.filter(models.CentreActivity.is_deleted == False)

    if not db_centre_activities:
        raise HTTPException(status_code=404, detail="No Centre Activities found")
    
    return (
        db_centre_activities.order_by(models.CentreActivity.start_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_centre_activity(
        db: Session, 
        centre_activity_data: schemas.CentreActivityUpdate, 
        current_user_info: dict,
        correlation_id: str = None
        ):
    
    # Check if centre activity record exists. Allow update of is_deleted back to False.
    db_centre_activity = db.query(models.CentreActivity).filter(
        models.CentreActivity.id == centre_activity_data.id,
        ).first()
    if not db_centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found")
    
    # Validate dependencies and check for duplicates (excluding current record)
    _validate_activity_exists(db, centre_activity_data.activity_id)
    
    # Validate + detect changes
    changes = _validate_and_detect_changes(
        db, centre_activity_data, db_centre_activity, exclude_id=centre_activity_data.id
    )

    if not changes:
        logger.info(f"No changes detected for centre activity {db_centre_activity.id}")
        return db_centre_activity

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        original_activity_dict = _centre_activity_to_dict(db_centre_activity)
        original_data_dict = serialize_data(model_to_dict(db_centre_activity))

        # 2. Update the record (changes already validated)
        timestamp = datetime.utcnow()
        modified_by_id = current_user_info.get("id") or centre_activity_data.modified_by_id

        # Update the fields of the CentreActivity instance
        update_data = centre_activity_data.model_dump(exclude={'id'}, exclude_unset=True)
        for field, value in update_data.items():
            if field not in {'created_by_id', 'modified_by_id', 'created_date', 'modified_date'}:
                setattr(db_centre_activity, field, value)
        
        db_centre_activity.modified_by_id = modified_by_id
        db_centre_activity.modified_date = timestamp

        db.flush()

        # 3. Create outbox event (we know there are changes)
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'CENTRE_ACTIVITY_UPDATED',
            'centre_activity_id': db_centre_activity.id,
            'old_data': original_activity_dict,
            'new_data': _centre_activity_to_dict(db_centre_activity),
            'changes': changes,
            'modified_by': modified_by_id,
            'modified_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='CENTRE_ACTIVITY_UPDATED',
            aggregate_id=db_centre_activity.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity.updated.{db_centre_activity.id}",
            correlation_id=correlation_id,
            created_by=modified_by_id
        )

        # 4. Log the action
        updated_data_dict = serialize_data(centre_activity_data.model_dump())
        log_crud_action(
            action=ActionType.UPDATE,
            user=modified_by_id,
            user_full_name=current_user_info.get("fullname"),
            message="Updated Centre Activity",
            table="CENTRE_ACTIVITY",
            entity_id=db_centre_activity.id,
            original_data=original_data_dict,
            updated_data=updated_data_dict
        )

        # 5. Commit atomically
        db.commit()
        db.refresh(db_centre_activity)
        
        logger.info(f"Updated centre activity {db_centre_activity.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return db_centre_activity

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update centre activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating Centre Activity: {str(e)}")

def delete_centre_activity(
        db: Session, 
        centre_activity_id: int, 
        current_user_info: dict,
        correlation_id: str = None
        ):
    
    # Check if centre activity record is already deleted
    db_centre_activity = db.query(models.CentreActivity).filter(
        models.CentreActivity.id == centre_activity_id, 
        models.CentreActivity.is_deleted == False
        ).first()
    
    if not db_centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found or deleted")
    
    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        activity_dict = _centre_activity_to_dict(db_centre_activity)

        # 2. Perform soft delete
        timestamp = datetime.utcnow()
        modified_by_id = current_user_info.get("id") or db_centre_activity.modified_by_id
        
        db_centre_activity.is_deleted = True
        db_centre_activity.modified_by_id = modified_by_id        
        db_centre_activity.modified_date = timestamp
        
        db.flush()

        # 3. Create outbox event
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'CENTRE_ACTIVITY_DELETED',
            'centre_activity_id': db_centre_activity.id,
            'centre_activity_data': activity_dict,
            'deleted_by': modified_by_id,
            'deleted_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='CENTRE_ACTIVITY_DELETED',
            aggregate_id=db_centre_activity.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity.deleted.{db_centre_activity.id}",
            correlation_id=correlation_id,
            created_by=modified_by_id
        )

        # 4. Log the action
        original_data_dict = serialize_data(model_to_dict(db_centre_activity))
        log_crud_action(
            action=ActionType.DELETE,
            user=modified_by_id,
            user_full_name=current_user_info.get("fullname"),
            message="Deleted Centre Activity",
            table="CENTRE_ACTIVITY",
            entity_id=db_centre_activity.id,
            original_data=original_data_dict,
            updated_data=None
        )

        # 5. Commit atomically
        db.commit()
        db.refresh(db_centre_activity)
        
        logger.info(f"Deleted centre activity {db_centre_activity.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return db_centre_activity

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete centre activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting Centre Activity: {str(e)}")

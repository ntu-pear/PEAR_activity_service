import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.models.centre_activity_model as models
import app.schemas.centre_activity_schema as schemas
from app.crud.activity_crud import get_activity_by_id
from app.logger.logger_utils import (
    ActionType,
    log_crud_action,
    model_to_dict,
    serialize_data,
)

from ..services.outbox_service import generate_correlation_id, get_outbox_service

logger = logging.getLogger(__name__)

def _centre_activity_to_dict(activity) -> Dict[str, Any]:
    """Convert centre activity model to dictionary for messaging"""
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


# Helper validation functions
def _validate_activity_exists(db: Session, activity_id: int):
    """Validate that activity exists"""
    activity = get_activity_by_id(db, activity_id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

def _check_centre_activity_duplicate(
    db: Session,
    centre_activity_data: Union[schemas.CentreActivityCreate, schemas.CentreActivityUpdate],
    exclude_id: int = None
):
    """Check if Centre Activity with same essential fields already exists"""
    essential_fields = {
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

    query = db.query(models.CentreActivity).filter_by(**essential_fields)
    
    if exclude_id is not None:
        query = query.filter(models.CentreActivity.id != exclude_id)
    
    existing_centre_activity = query.first()
    
    if existing_centre_activity:
        raise HTTPException(status_code=400,
                            detail={
                                "message": "Centre Activity with these attributes already exists or deleted",
                                "existing_id": str(existing_centre_activity.id),
                                "existing_is_deleted": existing_centre_activity.is_deleted
                            })

def create_centre_activity(
        db: Session, 
        centre_activity_data: schemas.CentreActivityCreate, 
        current_user_info: dict,
        correlation_id: str = None
        ):
    
    # Validate dependencies and check for duplicates
    _validate_activity_exists(db, centre_activity_data.activity_id)
    _check_centre_activity_duplicate(db, centre_activity_data)
    
    db_centre_activity = models.CentreActivity(**centre_activity_data.model_dump())
    current_user_id = current_user_info.get("id") or centre_activity_data.created_by_id
    db_centre_activity.created_by_id = current_user_id
    db.add(db_centre_activity)
    db.flush()  # Get the ID without committing    
    try:
        
        # Create outbox event in the same transaction
        outbox_service = get_outbox_service()
        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = generate_correlation_id()
            
        event_payload = {
            'event_type': 'CENTRE_ACTIVITY_CREATED',
            'centre_activity_id': db_centre_activity.id,
            'centre_activity_data': _centre_activity_to_dict(db_centre_activity),
            'created_by': current_user_info.get("id"),
            'created_by_name': current_user_info.get("fullname"),
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='CENTRE_ACTIVITY_CREATED',
            aggregate_id=db_centre_activity.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity.created.{db_centre_activity.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id")
        )
        
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
        
        db.commit()
        db.refresh(db_centre_activity)
        logger.info(f"Created centre activity {db_centre_activity.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Centre Activity: {str(e)}")
    
    return db_centre_activity


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
        ):
    
    # Check if centre activity record exists. Allow update of is_deleted back to False.
    db_centre_activity = db.query(models.CentreActivity).filter(
        models.CentreActivity.id == centre_activity_data.id,
        ).first()
    if not db_centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found")
    
    # Validate dependencies and check for duplicates (excluding current record)
    _validate_activity_exists(db, centre_activity_data.activity_id)
    _check_centre_activity_duplicate(db, centre_activity_data, exclude_id=centre_activity_data.id)
    
    original_data_dict = serialize_data(model_to_dict(db_centre_activity))
    updated_data_dict = serialize_data(centre_activity_data.model_dump())

    modified_by_id = current_user_info.get("id") or centre_activity_data.modified_by_id
    # Update the fields of the CentreActivity instance
    for field in schemas.CentreActivityUpdate.model_fields:
        if field != "Id" and hasattr(centre_activity_data, field):
            setattr(db_centre_activity, field, getattr(centre_activity_data, field))
    db_centre_activity.modified_by_id = modified_by_id
    db_centre_activity.modified_date = datetime.now()

    try:
        db.commit()
        db.refresh(db_centre_activity)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Centre Activity: {str(e)}")

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
    return db_centre_activity

def delete_centre_activity(
        db: Session, 
        centre_activity_id: int, 
        current_user_info: dict
        ):
    
    # Check if centre activity record is already deleted
    db_centre_activity = db.query(models.CentreActivity).filter(
        models.CentreActivity.id == centre_activity_id, 
        models.CentreActivity.is_deleted == False
        ).first()
    
    if not db_centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found or deleted")
    
    modified_by_id = current_user_info.get("id") or db_centre_activity.modified_by_id
    db_centre_activity.is_deleted = True
    db_centre_activity.modified_by_id = modified_by_id        
    db_centre_activity.modified_date = datetime.now()
    
    try:
        db.commit()
        db.refresh(db_centre_activity)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Centre Activity: {str(e)}")

    original_data_dict = serialize_data(model_to_dict(db_centre_activity))
    log_crud_action(
        action=ActionType.DELETE,
        user=modified_by_id,
        user_full_name= current_user_info.get("fullname"),
        message="Deleted Centre Activity",
        table="CENTRE_ACTIVITY",
        entity_id=db_centre_activity.id,
        original_data=original_data_dict,
        updated_data=None
    )
    return db_centre_activity
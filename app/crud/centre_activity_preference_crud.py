from typing import Dict, Any, Optional, Union
from sqlalchemy.orm import Session
import app.models.centre_activity_preference_model as models
import app.schemas.centre_activity_preference_schema as schemas
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from ..services.outbox_service import get_outbox_service, generate_correlation_id
from fastapi import HTTPException
from datetime import datetime
import app.services.patient_service as patient_service
import logging

logger = logging.getLogger(__name__)

# Helper validation functions
def _validate_patient_exists(patient_id: int, current_user_info: dict):
    """Validate that patient exists and is accessible"""
    try:
        if current_user_info.get('bearer_token'):   # Required_auth is false
            patient_data = patient_service.get_patient_by_id(
                require_auth=True,         
                bearer_token=current_user_info.get('bearer_token', ''),
                patient_id=patient_id
            )
            
            if patient_data.status_code != 200:
                raise HTTPException(
                    status_code=404,
                    detail="Patient not found or not accessible"
                )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

def _validate_caregiver_supervisor_allocation(patient_id: int, current_user_info: dict, action: str = "perform action on"):
    """Validate that caregiver/supervisor is assigned to the patient"""
    try:
        if current_user_info.get('bearer_token'):   # Required_auth is false
            get_patient_allocation_data = patient_service.get_patient_allocation_by_patient_id(
                require_auth=True, 
                bearer_token=current_user_info.get('bearer_token', ''), 
                patient_id=patient_id
            )
            if get_patient_allocation_data.status_code != 200:
                raise HTTPException(
                    status_code=404,
                    detail="Patient allocation not found or not accessible"
                )
            
            if (current_user_info.get('role_name') == "CAREGIVER" and 
                current_user_info.get('id') != get_patient_allocation_data.json().get('caregiverId')) or \
            (current_user_info.get('role_name') == "SUPERVISOR" and 
                current_user_info.get('id') != get_patient_allocation_data.json().get('supervisorId')):
                raise HTTPException(
                    status_code=403,
                    detail=f"You do not have permission to {action} a Centre Activity Preference for this Patient. \n" \
                    f"Role: {current_user_info.get('role_name')}, " \
                    f"User ID: {current_user_info.get('id')}, " \
                )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

def _validate_centre_activity_exists(db: Session, centre_activity_id: int):
    """Validate that centre activity exists"""
    existing_centre_activity = get_centre_activity_by_id(db, centre_activity_id=centre_activity_id)
    if not existing_centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found")

def _validate_and_detect_changes(
    db: Session,
    centre_activity_preference_data: Union[schemas.CentreActivityPreferenceCreate, schemas.CentreActivityPreferenceUpdate],
    db_centre_activity_preference = None,
    exclude_id: int = None
):
    """
    Universal function for duplicate validation and change detection.
    - For CREATE: Only validates duplicates (db_centre_activity_preference=None)
    - For UPDATE: Validates duplicates AND detects changes (db_centre_activity_preference provided)
    Returns changes dict for updates, None for creates, raises HTTPException if duplicate.
    """
    # Define essential business fields
    essential_fields = {
        "centre_activity_id", "patient_id", "is_like"
    }
    
    # For CREATE operations - just check duplicates
    if db_centre_activity_preference is None:
        query = db.query(models.CentreActivityPreference).filter(
            models.CentreActivityPreference.centre_activity_id == centre_activity_preference_data.centre_activity_id,
            models.CentreActivityPreference.patient_id == centre_activity_preference_data.patient_id,
            models.CentreActivityPreference.is_deleted == False
        )
        
        if exclude_id is not None:
            query = query.filter(models.CentreActivityPreference.id != exclude_id)
        
        existing_centre_activity_preference = query.first()
        
        if existing_centre_activity_preference:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Centre Activity Preference with these attributes already exists or deleted",
                    "existing_id": str(existing_centre_activity_preference.id),
                    "existing_is_deleted": existing_centre_activity_preference.is_deleted
                }
            )
        return None  # No changes to return for create
    
    # For UPDATE operations - detect changes AND validate duplicates
    audit_fields = {'created_by_id', 'modified_by_id', 'created_date', 'modified_date'}
    update_data = centre_activity_preference_data.model_dump(exclude={'centre_activity_preference_id'}, exclude_unset=True)
    changes = {}
    essential_field_changes = {}
    
    # Single pass: detect all changes
    for field, new_value in update_data.items():
        if field not in audit_fields and hasattr(db_centre_activity_preference, field):
            old_value = getattr(db_centre_activity_preference, field)
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
        query = db.query(models.CentreActivityPreference).filter(
            models.CentreActivityPreference.centre_activity_id == essential_field_changes.get('centre_activity_id', getattr(db_centre_activity_preference, 'centre_activity_id')),
            models.CentreActivityPreference.patient_id == essential_field_changes.get('patient_id', getattr(db_centre_activity_preference, 'patient_id')),
            models.CentreActivityPreference.is_deleted == False
        )
        
        if exclude_id is not None:
            query = query.filter(models.CentreActivityPreference.id != exclude_id)
        
        existing_centre_activity_preference = query.first()
        
        if existing_centre_activity_preference:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Centre Activity Preference with these attributes already exists or deleted",
                    "existing_id": str(existing_centre_activity_preference.id),
                    "existing_is_deleted": existing_centre_activity_preference.is_deleted
                }
            )
    
    return changes

def _preference_to_dict(preference) -> Dict[str, Any]:
    """Convert centre activity preference model to dictionary for messaging"""
    try:
        if hasattr(preference, '__dict__'):
            preference_dict = {}
            for key, value in preference.__dict__.items():
                if not key.startswith('_'):
                    # Convert datetime objects to ISO format strings
                    if hasattr(value, 'isoformat'):
                        preference_dict[key] = value.isoformat()
                    else:
                        preference_dict[key] = value
            return preference_dict
        else:
            return {}
    except Exception as e:
        logger.error(f"Error converting preference to dict: {str(e)}")
        return {}

def create_centre_activity_preference(
        db: Session,
        centre_activity_preference_data: schemas.CentreActivityPreferenceCreate,
        current_user_info: dict,
        correlation_id: str = None
        ):

    # Validate all dependencies and permissions
    _validate_and_detect_changes(db, centre_activity_preference_data)
    
    _validate_centre_activity_exists(db, centre_activity_preference_data.centre_activity_id)
    _validate_patient_exists(centre_activity_preference_data.patient_id, current_user_info)
    _validate_caregiver_supervisor_allocation(centre_activity_preference_data.patient_id, current_user_info, "create")

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Create Centre Activity Preference
        timestamp = datetime.utcnow()
        current_user_id = current_user_info.get("id") or centre_activity_preference_data.created_by_id
        
        db_centre_activity_preference = models.CentreActivityPreference(**centre_activity_preference_data.model_dump())
        db_centre_activity_preference.created_by_id = current_user_id
        db_centre_activity_preference.modified_by_id = current_user_id
        db_centre_activity_preference.created_date = timestamp
        db_centre_activity_preference.modified_date = timestamp
        
        db.add(db_centre_activity_preference)
        db.flush()  # Get the ID without committing

        # 2. Create outbox event in the same transaction
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_PREFERENCE_CREATED',
            'preference_id': db_centre_activity_preference.id,
            'preference_data': _preference_to_dict(db_centre_activity_preference),
            'created_by': current_user_id,
            'created_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_PREFERENCE_CREATED',
            aggregate_id=db_centre_activity_preference.id,
            payload=event_payload,
            routing_key=f"activity.preference.created.{db_centre_activity_preference.id}",
            correlation_id=correlation_id,
            created_by=current_user_id
        )

        # 3. Log the action
        updated_data_dict = serialize_data(centre_activity_preference_data.model_dump())
        log_crud_action(
            action=ActionType.CREATE,
            user=current_user_id,
            user_full_name=current_user_info.get("fullname"),
            message="Created a new Centre Activity Preference",
            table="CENTRE_ACTIVITY_PREFERENCE",
            entity_id=db_centre_activity_preference.id,
            original_data=None,
            updated_data=updated_data_dict
        )

        # 4. Commit both preference and outbox event atomically
        db.commit()
        db.refresh(db_centre_activity_preference)
        
        logger.info(f"Created preference {db_centre_activity_preference.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return db_centre_activity_preference

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create centre activity preference: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")

def get_centre_activity_preference_by_id(
        db: Session, 
        centre_activity_preference_id: int,
        include_deleted: bool = False
    ):
    centre_activity_preference = db.query(models.CentreActivityPreference)

    if not include_deleted:
        centre_activity_preference = centre_activity_preference.filter(models.CentreActivityPreference.is_deleted == False)

    centre_activity_preference = centre_activity_preference.filter(
        models.CentreActivityPreference.id == centre_activity_preference_id
    ).first()

    if not centre_activity_preference:
        raise HTTPException(status_code=404, detail="Centre Activity Preference not found")
    
    return centre_activity_preference

def get_centre_activity_preferences_by_patient_id(
        db: Session,
        patient_id: int,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
    ):
    
    centre_activity_preferences = db.query(models.CentreActivityPreference)
    if not include_deleted:
        centre_activity_preferences = centre_activity_preferences.filter(models.CentreActivityPreference.is_deleted == False)

    patient_centre_activity_preference = centre_activity_preferences.filter(
        models.CentreActivityPreference.patient_id == patient_id
    )

    if not patient_centre_activity_preference:
        raise HTTPException(status_code=404, detail="No Centre Activity Preferences found for this Patient")

    patient_centre_activity_preference = patient_centre_activity_preference.order_by(models.CentreActivityPreference.created_date).offset(skip).limit(limit).all()
    return patient_centre_activity_preference

def get_centre_activity_preferences(
        db: Session,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
    ):
    centre_activity_preferences = db.query(models.CentreActivityPreference)

    if not include_deleted:
        centre_activity_preferences = centre_activity_preferences.filter(models.CentreActivityPreference.is_deleted == False)

    centre_activity_preferences = centre_activity_preferences.order_by(models.CentreActivityPreference.patient_id).offset(skip).limit(limit).all()

    return centre_activity_preferences

def update_centre_activity_preference_by_id(
        db: Session,
        centre_activity_preference_data: schemas.CentreActivityPreferenceUpdate,
        current_user_info: dict,
        correlation_id: str = None
        ):
    
    centre_activity_preference_id = centre_activity_preference_data.centre_activity_preference_id

    # Check if the Centre Activity Preference exists
    existing_centre_activity_preference = db.query(models.CentreActivityPreference).filter(
        models.CentreActivityPreference.id == centre_activity_preference_id,
    ).first()
    
    if not existing_centre_activity_preference:
        raise HTTPException(status_code=404, detail="Centre Activity Preference not found")
    
    # Validate all dependencies and permissions
    _validate_centre_activity_exists(db, centre_activity_preference_data.centre_activity_id)
    _validate_patient_exists(centre_activity_preference_data.patient_id, current_user_info)
    _validate_caregiver_supervisor_allocation(centre_activity_preference_data.patient_id, current_user_info, "update")
    
    # Validate + detect changes
    changes = _validate_and_detect_changes(
        db, centre_activity_preference_data, existing_centre_activity_preference, exclude_id=centre_activity_preference_id
    )

    if not changes:
        logger.info(f"No changes detected for centre activity preference {existing_centre_activity_preference.id}")
        return existing_centre_activity_preference

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        original_preference_dict = _preference_to_dict(existing_centre_activity_preference)
        original_data_dict = serialize_data(model_to_dict(existing_centre_activity_preference))

        # 2. Update the record (changes already validated)
        timestamp = datetime.utcnow()
        modified_by_id = current_user_info.get("id") or centre_activity_preference_data.modified_by_id

        # Update the fields of the preference instance
        update_data = centre_activity_preference_data.model_dump(exclude={'centre_activity_preference_id'}, exclude_unset=True)
        for field, value in update_data.items():
            if field not in {'created_by_id', 'modified_by_id', 'created_date', 'modified_date'}:
                setattr(existing_centre_activity_preference, field, value)
        
        existing_centre_activity_preference.modified_by_id = modified_by_id
        existing_centre_activity_preference.modified_date = timestamp

        db.flush()

        # 3. Create outbox event (we know there are changes)
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_PREFERENCE_UPDATED',
            'preference_id': existing_centre_activity_preference.id,
            'old_data': original_preference_dict,
            'new_data': _preference_to_dict(existing_centre_activity_preference),
            'changes': changes,  # Already computed by _validate_and_detect_changes
            'modified_by': modified_by_id,
            'modified_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_PREFERENCE_UPDATED',
            aggregate_id=existing_centre_activity_preference.id,
            payload=event_payload,
            routing_key=f"activity.preference.updated.{existing_centre_activity_preference.id}",
            correlation_id=correlation_id,
            created_by=modified_by_id
        )

        # 4. Log the action
        updated_data_dict = serialize_data(centre_activity_preference_data.model_dump())
        log_crud_action(
            action=ActionType.UPDATE,
            user=modified_by_id,
            user_full_name=current_user_info.get("fullname"),
            message="Updated Centre Activity Preference",
            table="CENTRE_ACTIVITY_PREFERENCE",
            entity_id=existing_centre_activity_preference.id,
            original_data=original_data_dict,
            updated_data=updated_data_dict
        )

        # 5. Commit atomically
        db.commit()
        db.refresh(existing_centre_activity_preference)
        
        logger.info(f"Updated preference {existing_centre_activity_preference.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return existing_centre_activity_preference

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update centre activity preference: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")


def delete_centre_activity_preference_by_id(
    centre_activity_preference_id: int,
    db: Session,
    current_user_info: dict,
    correlation_id: str = None
):
    # Check if the Centre Activity Preference exists
    db_centre_activity_preference = db.query(models.CentreActivityPreference).filter(
        models.CentreActivityPreference.id == centre_activity_preference_id,
        models.CentreActivityPreference.is_deleted == False
    ).first()

    if not db_centre_activity_preference:
        raise HTTPException(status_code=404, detail="Centre Activity Preference not found or deleted")

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        preference_dict = _preference_to_dict(db_centre_activity_preference)

        # 2. Perform soft delete
        timestamp = datetime.utcnow()
        
        db_centre_activity_preference.is_deleted = True
        db_centre_activity_preference.modified_by_id = current_user_info.get("id")
        db_centre_activity_preference.modified_date = timestamp
        
        db.flush()

        # 3. Create outbox event
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_PREFERENCE_DELETED',
            'preference_id': db_centre_activity_preference.id,
            'preference_data': preference_dict,
            'deleted_by': current_user_info.get("id"),
            'deleted_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_PREFERENCE_DELETED',
            aggregate_id=db_centre_activity_preference.id,
            payload=event_payload,
            routing_key=f"activity.preference.deleted.{db_centre_activity_preference.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id")
        )

        # 4. Log the action
        log_crud_action(
            action=ActionType.DELETE,
            user=current_user_info.get("id"),
            user_full_name=current_user_info.get("fullname"),
            message="Deleted Centre Activity Preference",
            table="CENTRE_ACTIVITY_PREFERENCE",
            entity_id=db_centre_activity_preference.id,
            original_data=model_to_dict(db_centre_activity_preference),
            updated_data=None
        )

        # 5. Commit atomically
        db.commit()
        db.refresh(db_centre_activity_preference)
        
        logger.info(f"Deleted preference {db_centre_activity_preference.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return db_centre_activity_preference

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete centre activity preference: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")

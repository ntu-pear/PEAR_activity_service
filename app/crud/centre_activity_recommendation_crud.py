from sqlalchemy.orm import Session
from typing import Union, Dict, Any
import app.models.centre_activity_recommendation_model as models
import app.schemas.centre_activity_recommendation_schema as schemas
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

def _validate_doctor_allocation(patient_id: int, current_user_info: dict, action: str = "perform action on"):
    """Validate that doctor is assigned to the patient"""
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
            
            if (current_user_info.get('role_name') == "DOCTOR" and 
                current_user_info.get('id') != get_patient_allocation_data.json().get('doctorId')):
                raise HTTPException(
                    status_code=403,
                    detail=f"You do not have permission to {action} a Centre Activity Recommendation for this Patient. \n" \
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
    centre_activity_recommendation_data: Union[schemas.CentreActivityRecommendationCreate, schemas.CentreActivityRecommendationUpdate],
    db_centre_activity_recommendation = None,
    exclude_id: int = None
):
    """
    Universal function for duplicate validation and change detection.
    - For CREATE: Only validates duplicates (db_centre_activity_recommendation=None)
    - For UPDATE: Validates duplicates AND detects changes (db_centre_activity_recommendation provided)
    Returns changes dict for updates, None for creates, raises HTTPException if duplicate.
    """
    # Define essential business fields
    essential_fields = {
        "centre_activity_id", "patient_id"
    }
    
    # For CREATE operations - just check duplicates
    if db_centre_activity_recommendation is None:
        query = db.query(models.CentreActivityRecommendation).filter(
            models.CentreActivityRecommendation.centre_activity_id == centre_activity_recommendation_data.centre_activity_id,
            models.CentreActivityRecommendation.patient_id == centre_activity_recommendation_data.patient_id,
            models.CentreActivityRecommendation.is_deleted == False
        )
        
        if exclude_id is not None:
            query = query.filter(models.CentreActivityRecommendation.id != exclude_id)
        
        existing_centre_activity_recommendation = query.first()
        
        if existing_centre_activity_recommendation:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Centre Activity Recommendation with these attributes already exists",
                    "existing_id": str(existing_centre_activity_recommendation.id),
                    "existing_is_deleted": existing_centre_activity_recommendation.is_deleted
                }
            )
        return None  # No changes to return for create
    
    # For UPDATE operations - detect changes AND validate duplicates
    audit_fields = {'created_by_id', 'modified_by_id', 'created_date', 'modified_date'}
    update_data = centre_activity_recommendation_data.model_dump(exclude={'centre_activity_recommendation_id'}, exclude_unset=True)
    changes = {}
    essential_field_changes = {}
    
    # Single pass: detect all changes
    for field, new_value in update_data.items():
        if field not in audit_fields and hasattr(db_centre_activity_recommendation, field):
            old_value = getattr(db_centre_activity_recommendation, field)
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
        query = db.query(models.CentreActivityRecommendation).filter(
            models.CentreActivityRecommendation.centre_activity_id == essential_field_changes.get('centre_activity_id', getattr(db_centre_activity_recommendation, 'centre_activity_id')),
            models.CentreActivityRecommendation.patient_id == essential_field_changes.get('patient_id', getattr(db_centre_activity_recommendation, 'patient_id')),
            models.CentreActivityRecommendation.is_deleted == False
        )
        
        if exclude_id is not None:
            query = query.filter(models.CentreActivityRecommendation.id != exclude_id)
        
        existing_centre_activity_recommendation = query.first()
        
        if existing_centre_activity_recommendation:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Centre Activity Recommendation with these attributes already exists",
                    "existing_id": str(existing_centre_activity_recommendation.id),
                    "existing_is_deleted": existing_centre_activity_recommendation.is_deleted
                }
            )
    
    return changes

def _recommendation_to_dict(recommendation) -> Dict[str, Any]:
    """Convert centre activity recommendation model to dictionary for messaging"""
    try:
        if hasattr(recommendation, '__dict__'):
            recommendation_dict = {}
            for key, value in recommendation.__dict__.items():
                if not key.startswith('_'):
                    # Convert datetime objects to ISO format strings
                    if hasattr(value, 'isoformat'):
                        recommendation_dict[key] = value.isoformat()
                    else:
                        recommendation_dict[key] = value
            return recommendation_dict
        else:
            return {}
    except Exception as e:
        logger.error(f"Error converting recommendation to dict: {str(e)}")
        return {}

def create_centre_activity_recommendation(
        db: Session,
        centre_activity_recommendation_data: schemas.CentreActivityRecommendationCreate,
        current_user_info: dict,
        correlation_id: str = None
        ):

    current_user_id = current_user_info.get("id") or centre_activity_recommendation_data.created_by_id
    
    # Validate all dependencies and permissions
    _validate_and_detect_changes(
        db, 
        centre_activity_recommendation_data
    )
    
    _validate_centre_activity_exists(db, centre_activity_recommendation_data.centre_activity_id)
    _validate_patient_exists(centre_activity_recommendation_data.patient_id, current_user_info)
    _validate_doctor_allocation(centre_activity_recommendation_data.patient_id, current_user_info, "create")

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Create Centre Activity Recommendation
        timestamp = datetime.now()
        
        db_centre_activity_recommendation = models.CentreActivityRecommendation(**centre_activity_recommendation_data.model_dump())
        db_centre_activity_recommendation.created_by_id = current_user_id
        db_centre_activity_recommendation.modified_by_id = current_user_id
        db_centre_activity_recommendation.doctor_id = current_user_id  # Only doctor can create recommendation
        db_centre_activity_recommendation.created_date = timestamp
        db_centre_activity_recommendation.modified_date = timestamp
        
        db.add(db_centre_activity_recommendation)
        db.flush()  # Get the ID without committing

        # 2. Create outbox event in the same transaction
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_RECOMMENDATION_CREATED',
            'recommendation_id': db_centre_activity_recommendation.id,
            'recommendation_data': _recommendation_to_dict(db_centre_activity_recommendation),
            'created_by': current_user_id,
            'created_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_RECOMMENDATION_CREATED',
            aggregate_id=db_centre_activity_recommendation.id,
            payload=event_payload,
            routing_key=f"activity.recommendation.created.{db_centre_activity_recommendation.id}",
            correlation_id=correlation_id,
            created_by=current_user_id
        )

        # 3. Log the action
        updated_data_dict = serialize_data(centre_activity_recommendation_data.model_dump())
        log_crud_action(
            action=ActionType.CREATE,
            user=current_user_id,
            user_full_name=current_user_info.get("fullname"),
            message="Created a new Centre Activity Recommendation",
            table="CENTRE_ACTIVITY_RECOMMENDATION",
            entity_id=db_centre_activity_recommendation.id,
            original_data=None,
            updated_data=updated_data_dict
        )

        # 4. Commit both recommendation and outbox event atomically
        db.commit()
        db.refresh(db_centre_activity_recommendation)
        
        logger.info(f"Created recommendation {db_centre_activity_recommendation.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return db_centre_activity_recommendation

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create centre activity recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating Centre Activity Recommendation: {str(e)}")


def get_centre_activity_recommendation_by_id(
        db: Session, 
        centre_activity_recommendation_id: int,
        include_deleted: bool = False
    ):
    centre_activity_recommendation = db.query(models.CentreActivityRecommendation)

    if not include_deleted:
        centre_activity_recommendation = centre_activity_recommendation.filter(models.CentreActivityRecommendation.is_deleted == False)

    centre_activity_recommendation = centre_activity_recommendation.filter(
        models.CentreActivityRecommendation.id == centre_activity_recommendation_id
    ).first()

    if not centre_activity_recommendation:
        raise HTTPException(status_code=404, detail="Centre Activity Recommendation not found")
    
    return centre_activity_recommendation


def get_all_centre_activity_recommendations(
        db: Session, 
        current_user_info: dict,
        include_deleted: bool = False
    ):
    centre_activity_recommendations = db.query(models.CentreActivityRecommendation)

    if not include_deleted:
        centre_activity_recommendations = centre_activity_recommendations.filter(models.CentreActivityRecommendation.is_deleted == False)

    centre_activity_recommendations = centre_activity_recommendations.all()

    if not centre_activity_recommendations:
        raise HTTPException(status_code=404, detail="No Centre Activity Recommendations found")
    
    return centre_activity_recommendations


def get_centre_activity_recommendations_by_patient_id(
        db: Session, 
        patient_id: int,
        current_user_info: dict,
        include_deleted: bool = False
    ):
    # Validate patient exists and permissions
    _validate_patient_exists(patient_id, current_user_info)
    _validate_doctor_allocation(patient_id, current_user_info, "view")

    centre_activity_recommendations = db.query(models.CentreActivityRecommendation).filter(
        models.CentreActivityRecommendation.patient_id == patient_id
    )

    if not include_deleted:
        centre_activity_recommendations = centre_activity_recommendations.filter(models.CentreActivityRecommendation.is_deleted == False)

    centre_activity_recommendations = centre_activity_recommendations.all()

    if not centre_activity_recommendations:
        raise HTTPException(status_code=404, detail=f"No Centre Activity Recommendations found for Patient ID {patient_id}")
    
    return centre_activity_recommendations


def update_centre_activity_recommendation(
        db: Session,
        centre_activity_recommendation_data: schemas.CentreActivityRecommendationUpdate,
        current_user_info: dict,
        correlation_id: str = None
):

    current_user_id = current_user_info.get("id") or centre_activity_recommendation_data.modified_by_id

    # Get existing Centre Activity Recommendation
    existing_centre_activity_recommendation = get_centre_activity_recommendation_by_id(
        db=db, 
        centre_activity_recommendation_id=centre_activity_recommendation_data.centre_activity_recommendation_id
    )

    # Validate dependencies and permissions
    _validate_centre_activity_exists(db, centre_activity_recommendation_data.centre_activity_id)
    _validate_patient_exists(centre_activity_recommendation_data.patient_id, current_user_info)
    _validate_doctor_allocation(centre_activity_recommendation_data.patient_id, current_user_info, "update")
    
    # Validate + detect changes
    changes = _validate_and_detect_changes(
        db, 
        centre_activity_recommendation_data,
        existing_centre_activity_recommendation,
        exclude_id=centre_activity_recommendation_data.centre_activity_recommendation_id
    )

    if not changes:
        logger.info(f"No changes detected for centre activity recommendation {existing_centre_activity_recommendation.id}")
        return existing_centre_activity_recommendation

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        original_recommendation_dict = _recommendation_to_dict(existing_centre_activity_recommendation)
        original_data_dict = serialize_data(model_to_dict(existing_centre_activity_recommendation))

        # 2. Update the record (changes already validated)
        timestamp = datetime.now()
        modified_by_id = current_user_id

        # Update the fields of the recommendation instance
        update_data = centre_activity_recommendation_data.model_dump(exclude={'centre_activity_recommendation_id'}, exclude_unset=True)
        for field, value in update_data.items():
            if field not in {'created_by_id', 'modified_by_id', 'created_date', 'modified_date'}:
                setattr(existing_centre_activity_recommendation, field, value)
        
        existing_centre_activity_recommendation.modified_by_id = modified_by_id
        existing_centre_activity_recommendation.modified_date = timestamp
        existing_centre_activity_recommendation.doctor_id = current_user_id  # Only doctor can update recommendation

        db.flush()

        # 3. Create outbox event (we know there are changes)
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_RECOMMENDATION_UPDATED',
            'recommendation_id': existing_centre_activity_recommendation.id,
            'old_data': original_recommendation_dict,
            'new_data': _recommendation_to_dict(existing_centre_activity_recommendation),
            'changes': changes,  # Already computed by _validate_and_detect_changes
            'modified_by': modified_by_id,
            'modified_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_RECOMMENDATION_UPDATED',
            aggregate_id=existing_centre_activity_recommendation.id,
            payload=event_payload,
            routing_key=f"activity.recommendation.updated.{existing_centre_activity_recommendation.id}",
            correlation_id=correlation_id,
            created_by=modified_by_id
        )

        # 4. Log the action
        updated_data_dict = serialize_data(centre_activity_recommendation_data.model_dump())
        log_crud_action(
            action=ActionType.UPDATE,
            user=modified_by_id,
            user_full_name=current_user_info.get("fullname"),
            message="Updated Centre Activity Recommendation",
            table="CENTRE_ACTIVITY_RECOMMENDATION",
            entity_id=existing_centre_activity_recommendation.id,
            original_data=original_data_dict,
            updated_data=updated_data_dict
        )

        # 5. Commit atomically
        db.commit()
        db.refresh(existing_centre_activity_recommendation)
        
        logger.info(f"Updated recommendation {existing_centre_activity_recommendation.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return existing_centre_activity_recommendation

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update centre activity recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating Centre Activity Recommendation: {str(e)}")


def delete_centre_activity_recommendation(
        db: Session,
        centre_activity_recommendation_id: int,
        current_user_info: dict,
        correlation_id: str = None
):
    # Get existing Centre Activity Recommendation
    existing_centre_activity_recommendation = get_centre_activity_recommendation_by_id(
        db=db, 
        centre_activity_recommendation_id=centre_activity_recommendation_id
    )

    # Validate permissions - check doctor allocation for patient
    _validate_patient_exists(existing_centre_activity_recommendation.patient_id, current_user_info)
    _validate_doctor_allocation(existing_centre_activity_recommendation.patient_id, current_user_info, "delete")

    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    try:
        # 1. Capture original data
        recommendation_dict = _recommendation_to_dict(existing_centre_activity_recommendation)

        # 2. Perform soft delete
        timestamp = datetime.now()
        current_user_id = current_user_info.get("id")
        
        existing_centre_activity_recommendation.is_deleted = True
        existing_centre_activity_recommendation.modified_by_id = current_user_id
        existing_centre_activity_recommendation.modified_date = timestamp
        
        db.flush()

        # 3. Create outbox event
        outbox_service = get_outbox_service()
        
        event_payload = {
            'event_type': 'ACTIVITY_RECOMMENDATION_DELETED',
            'recommendation_id': existing_centre_activity_recommendation.id,
            'recommendation_data': recommendation_dict,
            'deleted_by': current_user_id,
            'deleted_by_name': current_user_info.get("fullname"),
            'timestamp': timestamp.isoformat(),
            'correlation_id': correlation_id
        }
        
        outbox_event = outbox_service.create_event(
            db=db,
            event_type='ACTIVITY_RECOMMENDATION_DELETED',
            aggregate_id=existing_centre_activity_recommendation.id,
            payload=event_payload,
            routing_key=f"activity.recommendation.deleted.{existing_centre_activity_recommendation.id}",
            correlation_id=correlation_id,
            created_by=current_user_id
        )

        # 4. Log the action
        original_data_dict = serialize_data(model_to_dict(existing_centre_activity_recommendation))
        log_crud_action(
            action=ActionType.DELETE,
            user=current_user_id,
            user_full_name=current_user_info.get("fullname"),
            message="Deleted Centre Activity Recommendation",
            table="CENTRE_ACTIVITY_RECOMMENDATION",
            entity_id=existing_centre_activity_recommendation.id,
            original_data=original_data_dict,
            updated_data=None
        )

        # 5. Commit atomically
        db.commit()
        db.refresh(existing_centre_activity_recommendation)
        
        logger.info(f"Deleted recommendation {existing_centre_activity_recommendation.id} with outbox event {outbox_event.id} (correlation: {correlation_id})")
        return existing_centre_activity_recommendation

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete centre activity recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting Centre Activity Recommendation: {str(e)}")

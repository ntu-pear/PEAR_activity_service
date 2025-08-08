from sqlalchemy.orm import Session
import app.models.centre_activity_preference_model as models
import app.schemas.centre_activity_preference_schema as schemas
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from fastapi import HTTPException
from datetime import datetime, time
import app.services.patient_service as patient_service

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

def _check_centre_activity_preference_duplicate(
    db: Session, 
    centre_activity_id: int, 
    patient_id: int,
    is_like: bool,
    exclude_id: int = None
):
    """Check if Centre Activity Preference with same essential fields already exists"""
    query = db.query(models.CentreActivityPreference).filter(
        models.CentreActivityPreference.centre_activity_id == centre_activity_id,
        models.CentreActivityPreference.patient_id == patient_id,
        models.CentreActivityPreference.is_like == is_like,
        models.CentreActivityPreference.is_deleted == False
    )
    
    if exclude_id is not None:
        query = query.filter(models.CentreActivityPreference.id != exclude_id)
    
    existing_centre_activity_preference = query.first()
    
    if existing_centre_activity_preference:
        raise HTTPException(status_code=400,
                            detail={
                                "message": "Centre Activity Preference with these attributes already exists or deleted",
                                "existing_id": str(existing_centre_activity_preference.id),
                                "existing_is_deleted": existing_centre_activity_preference.is_deleted
                            })

def create_centre_activity_preference(
        db: Session,
        centre_activity_preference_data: schemas.CentreActivityPreferenceCreate,
        current_user_info: dict,
        ):

    # Validate all dependencies and permissions
    _check_centre_activity_preference_duplicate(
        db,
        centre_activity_preference_data.centre_activity_id,
        centre_activity_preference_data.patient_id,
        centre_activity_preference_data.is_like
    )
    
    _validate_centre_activity_exists(db, centre_activity_preference_data.centre_activity_id)
    _validate_patient_exists(centre_activity_preference_data.patient_id, current_user_info)
    _validate_caregiver_supervisor_allocation(centre_activity_preference_data.patient_id, current_user_info, "create")

    # Create Centre Activity Preference
    db_centre_activity_preference = models.CentreActivityPreference(**centre_activity_preference_data.model_dump())
    current_user_id = current_user_info.get("id") or centre_activity_preference_data.created_by_id
    db_centre_activity_preference.created_by_id = current_user_id
    db.add(db_centre_activity_preference)
    try:
        db.commit()
        db.refresh(db_centre_activity_preference)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Centre Activity Preference: {str(e)}")
    
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

    return db_centre_activity_preference

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
    
    # Check for duplicates (excluding current record)
    _check_centre_activity_preference_duplicate(
        db,
        centre_activity_preference_data.centre_activity_id,
        centre_activity_preference_data.patient_id,
        centre_activity_preference_data.is_like,
        exclude_id=centre_activity_preference_id
    )
    
    # Update the Centre Activity Preference
    db_centre_activity_preference = db.query(models.CentreActivityPreference).filter(
        models.CentreActivityPreference.id == centre_activity_preference_id,
    ).first()

    if not db_centre_activity_preference:
        raise HTTPException(status_code=404, detail="Centre Activity Preference not found")
    
    original_data_dict = serialize_data(model_to_dict(db_centre_activity_preference))
    modified_by_id = current_user_info.get("id") or centre_activity_preference_data.modified_by_id
    
    # Update the fields of the CentreActivityPreference instance
    for field in schemas.CentreActivityPreferenceUpdate.model_fields:
        if field != "id" and hasattr(centre_activity_preference_data, field):
            setattr(db_centre_activity_preference, field, getattr(centre_activity_preference_data, field))

    db_centre_activity_preference.modified_by_id = modified_by_id
    db_centre_activity_preference.modified_date = datetime.now()

    try:
        db.commit()
        db.refresh(db_centre_activity_preference)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Centre Activity Preference: {str(e)}")
    
    
    updated_data_dict = serialize_data(centre_activity_preference_data.model_dump())
    log_crud_action(
        action=ActionType.UPDATE,
        user=modified_by_id,
        user_full_name=current_user_info.get("fullname"),
        message="Updated Centre Activity Preference",
        table="CENTRE_ACTIVITY_PREFERENCE",
        entity_id=db_centre_activity_preference.id,
        original_data=original_data_dict,
        updated_data=updated_data_dict
    )
    
    return db_centre_activity_preference


def delete_centre_activity_preference_by_id(
    centre_activity_preference_id: int,
    db: Session,
    current_user_info: dict,
):
    # Check if the Centre Activity Preference exists
    db_centre_activity_preference = db.query(models.CentreActivityPreference).filter(
        models.CentreActivityPreference.id == centre_activity_preference_id,
        models.CentreActivityPreference.is_deleted == False
    ).first()

    if not db_centre_activity_preference:
        raise HTTPException(status_code=404, detail="Centre Activity Preference not found or deleted")
    
    # Soft delete the Centre Activity Preference
    db_centre_activity_preference.is_deleted = True
    db_centre_activity_preference.modified_by_id = current_user_info.get("id")
    db_centre_activity_preference.modified_date = datetime.now()

    try:
        db.commit()
        db.refresh(db_centre_activity_preference)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Centre Activity Preference: {str(e)}")
    
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
    
    return db_centre_activity_preference
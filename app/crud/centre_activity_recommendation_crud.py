from sqlalchemy.orm import Session
import app.models.centre_activity_recommendation_model as models
import app.schemas.centre_activity_recommendation_schema as schemas
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from fastapi import HTTPException
from datetime import datetime
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

def _check_centre_activity_recommendation_duplicate(
    db: Session, 
    centre_activity_id: int, 
    patient_id: int, 
    doctor_id: int, 
    exclude_id: int = None
):
    """Check if Centre Activity Recommendation with same essential fields already exists"""
    query = db.query(models.CentreActivityRecommendation).filter(
        models.CentreActivityRecommendation.centre_activity_id == centre_activity_id,
        models.CentreActivityRecommendation.patient_id == patient_id,
        models.CentreActivityRecommendation.doctor_id == doctor_id,
        models.CentreActivityRecommendation.is_deleted == False
    )
    
    if exclude_id is not None:
        query = query.filter(models.CentreActivityRecommendation.id != exclude_id)
    
    existing_centre_activity_recommendation = query.first()
    
    if existing_centre_activity_recommendation:
        raise HTTPException(status_code=400,
                            detail={
                                "message": "Centre Activity Recommendation with these attributes already exists",
                                "existing_id": str(existing_centre_activity_recommendation.id),
                                "existing_is_deleted": existing_centre_activity_recommendation.is_deleted
                            })

def create_centre_activity_recommendation(
        db: Session,
        centre_activity_recommendation_data: schemas.CentreActivityRecommendationCreate,
        current_user_info: dict,
        ):

    # Validate all dependencies and permissions
    _check_centre_activity_recommendation_duplicate(
        db, 
        centre_activity_recommendation_data.centre_activity_id,
        centre_activity_recommendation_data.patient_id,
        centre_activity_recommendation_data.doctor_id
    )
    
    _validate_centre_activity_exists(db, centre_activity_recommendation_data.centre_activity_id)
    _validate_patient_exists(centre_activity_recommendation_data.patient_id, current_user_info)
    _validate_doctor_allocation(centre_activity_recommendation_data.patient_id, current_user_info, "create")

    # Create Centre Activity Recommendation
    db_centre_activity_recommendation = models.CentreActivityRecommendation(**centre_activity_recommendation_data.model_dump())
    current_user_id = current_user_info.get("id") or centre_activity_recommendation_data.created_by_id
    db_centre_activity_recommendation.created_by_id = current_user_id
    db.add(db_centre_activity_recommendation)
    try:
        db.commit()
        db.refresh(db_centre_activity_recommendation)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Centre Activity Recommendation: {str(e)}")
    
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

    return db_centre_activity_recommendation


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
):

    # Get existing Centre Activity Recommendation
    existing_centre_activity_recommendation = get_centre_activity_recommendation_by_id(
        db=db, 
        centre_activity_recommendation_id=centre_activity_recommendation_data.centre_activity_recommendation_id
    )

    # Validate dependencies
    _check_centre_activity_recommendation_duplicate(
        db, 
        centre_activity_recommendation_data.centre_activity_id,
        centre_activity_recommendation_data.patient_id,
        centre_activity_recommendation_data.doctor_id,
        exclude_id=centre_activity_recommendation_data.centre_activity_recommendation_id
    )
    
    _validate_centre_activity_exists(db, centre_activity_recommendation_data.centre_activity_id)
    _validate_patient_exists(centre_activity_recommendation_data.patient_id, current_user_info)
    _validate_doctor_allocation(centre_activity_recommendation_data.patient_id, current_user_info, "update")

    # Store original data for logging
    original_data_dict = model_to_dict(existing_centre_activity_recommendation)
    original_data_dict = serialize_data(original_data_dict)

    # Update Centre Activity Recommendation
    for key, value in centre_activity_recommendation_data.model_dump(exclude={'centre_activity_recommendation_id'}).items():
        if hasattr(existing_centre_activity_recommendation, key) and value is not None:
            setattr(existing_centre_activity_recommendation, key, value)

    current_user_id = current_user_info.get("id") or centre_activity_recommendation_data.modified_by_id
    existing_centre_activity_recommendation.modified_by_id = current_user_id
    existing_centre_activity_recommendation.modified_date = datetime.now()

    try:
        db.commit()
        db.refresh(existing_centre_activity_recommendation)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Centre Activity Recommendation: {str(e)}")

    updated_data_dict = model_to_dict(existing_centre_activity_recommendation)
    updated_data_dict = serialize_data(updated_data_dict)

    log_crud_action(
        action=ActionType.UPDATE,
        user=current_user_id,
        user_full_name=current_user_info.get("fullname"),
        message="Updated a Centre Activity Recommendation",
        table="CENTRE_ACTIVITY_RECOMMENDATION",
        entity_id=existing_centre_activity_recommendation.id,
        original_data=original_data_dict,
        updated_data=updated_data_dict
    )

    return existing_centre_activity_recommendation


def delete_centre_activity_recommendation(
        db: Session,
        centre_activity_recommendation_id: int,
        current_user_info: dict,
):
    # Get existing Centre Activity Recommendation
    existing_centre_activity_recommendation = get_centre_activity_recommendation_by_id(
        db=db, 
        centre_activity_recommendation_id=centre_activity_recommendation_id
    )

    # Validate permissions - check doctor allocation for patient
    _validate_patient_exists(existing_centre_activity_recommendation.patient_id, current_user_info)
    _validate_doctor_allocation(existing_centre_activity_recommendation.patient_id, current_user_info, "delete")

    # Store original data for logging
    original_data_dict = model_to_dict(existing_centre_activity_recommendation)
    original_data_dict = serialize_data(original_data_dict)

    # Soft delete
    existing_centre_activity_recommendation.is_deleted = True
    current_user_id = current_user_info.get("id")
    existing_centre_activity_recommendation.modified_by_id = current_user_id
    existing_centre_activity_recommendation.modified_date = datetime.now()

    try:
        db.commit()
        db.refresh(existing_centre_activity_recommendation)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Centre Activity Recommendation: {str(e)}")

    updated_data_dict = model_to_dict(existing_centre_activity_recommendation)
    updated_data_dict = serialize_data(updated_data_dict)

    log_crud_action(
        action=ActionType.DELETE,
        user=current_user_id,
        user_full_name=current_user_info.get("fullname"),
        message="Deleted a Centre Activity Recommendation",
        table="CENTRE_ACTIVITY_RECOMMENDATION",
        entity_id=existing_centre_activity_recommendation.id,
        original_data=original_data_dict,
        updated_data=updated_data_dict
    )

    return existing_centre_activity_recommendation

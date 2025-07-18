from sqlalchemy.orm import Session
import app.models.centre_activity_model as models
import app.schemas.centre_activity_schema as schemas
from app.crud.activity_crud import get_activity_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from fastapi import HTTPException
from typing import List
from datetime import datetime

def create_centre_activity(
        db: Session, 
        centre_activity_data: schemas.CentreActivityCreate, 
        current_user_info: dict,
        ):
    
    # Check if the activity exists
    activity = get_activity_by_id(db, activity_id=centre_activity_data.activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    db_centre_activity = models.CentreActivity(
        **centre_activity_data.model_dump(), 
        modified_by_id=centre_activity_data.created_by_id,
        )
    
    # Check if the same centre_activity exists
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

    existing_centre_activity = db.query(models.CentreActivity).filter_by(**essential_fields).first()

    if existing_centre_activity:
        raise HTTPException(status_code=400, 
                            detail={
                                "message": "Centre Activity with these attributes already exists (including soft-deleted records)",
                                "existing_id": str(existing_centre_activity.id),
                                "existing_is_deleted": existing_centre_activity.is_deleted
                            })
 
    db.add(db_centre_activity)
    try:
        db.commit()
        db.refresh(db_centre_activity)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Centre Activity: {str(e)}")
    
    updated_data_dict = serialize_data(centre_activity_data.model_dump())
    log_crud_action(
        action=ActionType.CREATE,
        user=current_user_info.get("id") or centre_activity_data.created_by_id,
        user_full_name=current_user_info.get("fullname"),
        message="Created a new Centre Activity",
        table="CENTRE_ACTIVITY",
        entity_id=db_centre_activity.id,
        original_data=None,
        updated_data=updated_data_dict
    )   
    return db_centre_activity


def get_centre_activity_by_id(
        db: Session, 
        centre_activity_id: int,
        ):
    db_centre_activity = db.query(models.CentreActivity).filter(
        models.CentreActivity.id == centre_activity_id, 
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
    
    # Check if the activity to be updated exists
    activity = get_activity_by_id(db, activity_id=centre_activity_data.activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check if the same centre_activity exists
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

    existing_centre_activity = db.query(models.CentreActivity).filter(
        models.CentreActivity.id != centre_activity_data.id
    ).filter_by(
        **essential_fields
    ).first()
    
    if existing_centre_activity:
        raise HTTPException(status_code=400, 
                            detail={
                                "message": "Centre Activity with these attributes already exists (including soft-deleted records)",
                                "existing_id": str(existing_centre_activity.id),
                                "existing_is_deleted": existing_centre_activity.is_deleted
                            })
    
    original_data_dict = serialize_data(model_to_dict(db_centre_activity))
    updated_data_dict = serialize_data(centre_activity_data.model_dump())

    modified_by_id = current_user_info.get("id") or centre_activity_data.modified_by_id
    # Update the fields of the CentreActivity instance
    for field in schemas.CentreActivityUpdate.__fields__:
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
        raise HTTPException(status_code=404, detail="Centre Activity not found (including soft-deleted records)")
    
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
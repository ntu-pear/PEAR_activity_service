from sqlachemy.orm import Session
from app.models.centre_activity_model import CentreActivity
from app.schemas.centre_activity_schema import (
    CentreActivityCreate, 
    CentreActivityUpdate, 
)
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data
from fastapi import HTTPException
from typing import List
from datetime import datetime

def create_centre_activity(db: Session, centre_activity_data: CentreActivityCreate, user_full_name: str):
    db_centre_activity = CentreActivity(
        **centre_activity_data.model_dump(), 
        created_by_id=centre_activity_data.created_by_id, 
        modified_by_id=centre_activity_data.created_by_id)
    
    db.add(db_centre_activity)
    db.commit()
    db.refresh(db_centre_activity)

    updated_data_dict = serialize_data(centre_activity_data.model_dump())
    log_crud_action(
        action=ActionType.CREATE,
        user=centre_activity_data.created_by_id,
        user_full_name=user_full_name,
        message="Created a new Centre Activity",
        table="CENTRE_ACTIVITY",
        entity_id=db_centre_activity.id,
        original_data=None,
        updated_data=updated_data_dict
    )   

    return db_centre_activity

def get_centre_activity_by_id(db: Session, centre_activity_id: int):
    db_centre_activity = db.query(CentreActivity).filter(
        CentreActivity.id == centre_activity_id, 
        CentreActivity.is_deleted == False
        ).first()
    
    if not db_centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found")
    return db_centre_activity

def get_centre_activities(db: Session):
    db_centre_activities = db.query(CentreActivity).filter(
        CentreActivity.is_deleted==False
        ).all()
    return db_centre_activities

def update_centre_activity(db: Session, centre_activity_data: CentreActivityUpdate, user_full_name: str):
    db_centre_activity = db.query(CentreActivity).filter(
        CentreActivity.id == centre_activity_data.id,
        CentreActivity.is_deleted == False,
        ).first()
    if not db_centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found")
    
    #original_data_dict = serialize_data(db_centre_activity.model_dump())
    original_data_dict = db_centre_activity.__dict__.copy()
    updated_data_dict = serialize_data(centre_activity_data.model_dump())
    
    # Update the fields of the CentreActivity instance
    for field in CentreActivityUpdate.__fields__:
        if field != "Id" and hasattr(centre_activity_data, field):
            setattr(db_centre_activity, field, getattr(centre_activity_data, field))
    db_centre_activity.modified_by_id = centre_activity_data.modified_by_id
    db_centre_activity.modified_date = datetime.now()
    db.commit()
    db.refresh(db_centre_activity)
    log_crud_action(
        action=ActionType.UPDATE,
        user=centre_activity_data.modified_by_id,
        user_full_name=user_full_name,
        message="Updated Centre Activity",
        table="CENTRE_ACTIVITY",
        entity_id=db_centre_activity.id,
        original_data=original_data_dict,
        updated_data=updated_data_dict
    )
    return db_centre_activity

def delete_centre_activity(db: Session, centre_activity_id: int, modified_by_id: str, user_full_name: str):
    db_centre_activity = db.query(CentreActivity).filter(
        CentreActivity.id == centre_activity_id, 
        CentreActivity.is_deleted == False
        ).first()
    
    if not db_centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found")
    
    db_centre_activity.is_deleted = True
    db_centre_activity.modified_by_id = modified_by_id        
    db_centre_activity.modified_date = datetime.now()
    
    db.commit()
    db.refresh(db_centre_activity)

    log_crud_action(
        action=ActionType.DELETE,
        user=modified_by_id,
        user_full_name=user_full_name,
        message="Deleted Centre Activity",
        table="CENTRE_ACTIVITY",
        entity_id=db_centre_activity.id,
        original_data=db_centre_activity.__dict__.copy(),
        updated_data=None
    )

    return None





    

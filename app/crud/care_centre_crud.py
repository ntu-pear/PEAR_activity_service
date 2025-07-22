from sqlalchemy.orm import Session
import app.models.care_centre_model as models
import app.schemas.care_centre_schema as schemas
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from fastapi import HTTPException
from datetime import datetime, time

def create_care_centre(
        db: Session, 
        care_centre_data: schemas.CareCentreCreate, 
        current_user_info: dict,
        ):
    
    # Check if the same care centre exists
    essential_fields = {
        "name": care_centre_data.name,
        "country_code": care_centre_data.country_code,
        "address": care_centre_data.address,
        "postal_code": care_centre_data.postal_code,
        "contact_no": care_centre_data.contact_no,
        "email": care_centre_data.email,
        "no_of_devices_avail": care_centre_data.no_of_devices_avail,
        "working_hours": care_centre_data.working_hours,
        "remarks": care_centre_data.remarks
    }

    existing_care_centre = db.query(models.CareCentre).filter_by(**essential_fields).first()

    if existing_care_centre:
        raise HTTPException(status_code=400, 
                            detail={
                                "message": "Care Centre with these attributes already exists or deleted",
                                "existing_id": str(existing_care_centre.id),
                                "existing_is_deleted": existing_care_centre.is_deleted
                            })
    
    db_care_centre = models.CareCentre(**care_centre_data.model_dump())
    current_user_id = current_user_info.get("id") or care_centre_data.created_by_id
    db_care_centre.created_by_id = current_user_id
    db.add(db_care_centre)
    
    try:
        db.commit()
        db.refresh(db_care_centre)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Care Centre: {str(e)}")
    
    updated_data_dict = serialize_data(care_centre_data.model_dump())
    log_crud_action(
        action=ActionType.CREATE,
        user=current_user_info.get("id") or care_centre_data.created_by_id,
        user_full_name=current_user_info.get("fullname"),
        message="Created a new Care Centre",
        table="CARE_CENTRE",
        entity_id=db_care_centre.id,
        original_data=None,
        updated_data=updated_data_dict
    )   
    return db_care_centre

def get_care_centre_by_id(
        db: Session, 
        care_centre_id: int,
        include_deleted: bool = False
    ):
    care_centre = db.query(models.CareCentre)

    if not include_deleted:
        care_centre = care_centre.filter(models.CareCentre.is_deleted == False)
    
    care_centre = care_centre.filter(
        models.CareCentre.id == care_centre_id
        ).first()

    if not care_centre:
        raise HTTPException(status_code=404, detail="Care Centre not found")
    return care_centre

def get_care_centres(
        db: Session,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
    ):
    db_care_centres = db.query(models.CareCentre)

    # Exclude is_deleted=True records, else show all records if include_deleted is True
    if not include_deleted:
        db_care_centres = db_care_centres.filter(models.CareCentre.is_deleted == False)

    if not db_care_centres:
        raise HTTPException(status_code=404, detail="No Care Centres found")
    
    return (db_care_centres.order_by(
        models.CareCentre.name)
        .offset(skip)
        .limit(limit).all()
        )

def update_care_centre(
        db: Session,
        care_centre_data: schemas.CareCentreUpdate,
        current_user_info: dict,
):
    
    # Check if Care Centre record exists. Allow update of is_deleted back to False.
    db_care_centre = db.query(models.CareCentre).filter(
        models.CareCentre.id == care_centre_data.id,
        ).first()
    
    if not db_care_centre:
        raise HTTPException(status_code=404, detail="Care Centre not found")
    
    # Check if update creates a duplicate record
    essential_fields = {
        "name": care_centre_data.name,
        "country_code": care_centre_data.country_code,
        "address": care_centre_data.address,
        "postal_code": care_centre_data.postal_code,
        "contact_no": care_centre_data.contact_no,
        "email": care_centre_data.email,
        "no_of_devices_avail": care_centre_data.no_of_devices_avail,
        "working_hours": care_centre_data.working_hours,
        "remarks": care_centre_data.remarks
    }

    existing_care_centre = db.query(models.CareCentre).filter(
        models.CareCentre.id != care_centre_data.id,  # Exclude current record
    ).filter_by(
        **essential_fields
    ).first()

    if existing_care_centre:
        raise HTTPException(status_code=400, 
                            detail={
                                "message": "Care Centre with these attributes already exists or deleted",
                                "existing_id": str(existing_care_centre.id),
                                "existing_is_deleted": existing_care_centre.is_deleted
                            })
    
    original_data_dict = serialize_data(model_to_dict(db_care_centre))
    updated_data_dict = serialize_data(care_centre_data.model_dump())

    modified_by_id = current_user_info.get("id") or care_centre_data.modified_by_id
    # Update the fields of the CareCentre instance
    for field in schemas.CareCentreUpdate.__fields__:
        if field != "Id" and hasattr(care_centre_data, field):
            setattr(db_care_centre, field, getattr(care_centre_data, field))
    
    db_care_centre.modified_by_id = modified_by_id
    db_care_centre.modified_date = datetime.now()

    try:
        db.commit()
        db.refresh(db_care_centre)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Care Centre: {str(e)}")
    
    log_crud_action(
        action=ActionType.UPDATE,
        user=modified_by_id,
        user_full_name=current_user_info.get("fullname"),
        message="Updated Care Centre",
        table="CARE_CENTRE",
        entity_id=db_care_centre.id,
        original_data=original_data_dict,
        updated_data=updated_data_dict
    )
    return db_care_centre

def delete_care_centre(
        db: Session, 
        care_centre_id: int, 
        current_user_info: dict
        ):
    
    
    db_care_centre = db.query(models.CareCentre).filter(
        models.CareCentre.id == care_centre_id, 
        models.CareCentre.is_deleted == False
        ).first()
    
    # Check if Care Centre record is already deleted
    if not db_care_centre:
        raise HTTPException(status_code=404, detail="Care Centre not found or already deleted")

    db_care_centre.is_deleted = True
    db_care_centre.modified_by_id = current_user_info.get("id") or db_care_centre.modified_by_id
    db_care_centre.modified_date = datetime.now()
    try:
        db.commit()
        db.refresh(db_care_centre)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Care Centre: {str(e)}")
    
    original_data_dict = serialize_data(model_to_dict(db_care_centre))
    log_crud_action(
        action=ActionType.DELETE,
        user=db_care_centre.modified_by_id,
        user_full_name=current_user_info.get("fullname"),
        message="Deleted Care Centre",
        table="CARE_CENTRE",
        entity_id=db_care_centre.id,
        original_data=original_data_dict,
        updated_data=None
    )
    return db_care_centre
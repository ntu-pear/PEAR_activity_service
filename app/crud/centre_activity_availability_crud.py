from sqlalchemy.orm import Session
from sqlalchemy import func
import app.models.centre_activity_availability_model as models
import app.schemas.centre_activity_availability_schema as schemas
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from fastapi import HTTPException
from datetime import datetime, timezone

def check_for_duplicate_availability(
        db:Session,
        centre_activity_availability_data: schemas.CentreActivityAvailabilityCreate
    ):
    
    essential_fields = {
        "centre_activity_id": centre_activity_availability_data.centre_activity_id,
        "start_time": centre_activity_availability_data.start_time,
        "end_time": centre_activity_availability_data.end_time
    }
    
    existing_availability = db.query(models.CentreActivityAvailability).filter_by(**essential_fields).first()
    if existing_availability:
        raise HTTPException(status_code=400,
                detail = {
                    "message": "Centre Activity Availability with these attributes already exists or soft deleted.",
                    "existing_id": str(existing_availability.id),
                    "existing_is_deleted": existing_availability.is_deleted
                })
    
def check_availability_time_clash(
        db: Session,
        centre_activity_availability_data: schemas.CentreActivityAvailabilityCreate
    ):

    centre_activity_date = centre_activity_availability_data.start_time.date()
    centre_activity_timetable = db.query(models.CentreActivityAvailability).filter(
                                        func.date(models.CentreActivityAvailability.start_time) == centre_activity_date
                                    ).all()
    
    for timeslot in centre_activity_timetable:
        if centre_activity_availability_data.end_time <= timeslot.end_time and centre_activity_availability_data.start_time >= timeslot.start_time:
            raise HTTPException(status_code=400,
                detail = {
                    "message": "The centre activity availability you wish to create is clashing with another centre activity availability timing."
                })

def create_centre_activity_availability(
        db:Session,
        centre_activity_availability_data: schemas.CentreActivityAvailabilityCreate,
        current_user_info: dict
    ):

    centre_activity = get_centre_activity_by_id(db, centre_activity_id=centre_activity_availability_data.centre_activity_id)
    if not centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found.")
    
    db_centre_activity_availability = models.CentreActivityAvailability(**centre_activity_availability_data.model_dump())

    check_for_duplicate_availability(db, centre_activity_availability_data)

    current_user_id = current_user_info.get("id") or centre_activity_availability_data.created_by_id
    db_centre_activity_availability.created_by_id = current_user_id
    db.add(db_centre_activity_availability)

    try:
        db.commit()
        db.refresh(db_centre_activity_availability)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Centre Activity Availability: {str(e)}")
    
    updated_data_dict = serialize_data(centre_activity_availability_data.model_dump())

    log_crud_action(
        action = ActionType.CREATE,
        user = current_user_id,
        user_full_name = current_user_info.get("fullname"),
        message = "Created a new record.",
        table = "CENTRE_ACTIVITY_AVAILABILITY",
        entity_id = db_centre_activity_availability.id,
        original_data = None,
        updated_data = updated_data_dict
    )
    return db_centre_activity_availability


def get_centre_activity_availability_by_id(
        db: Session,
        centre_activity_availability_id: int,
        include_deleted: bool = False
    ):

    db_centre_activity_availability = db.query(models.CentreActivityAvailability).filter(
        models.CentreActivityAvailability.id == centre_activity_availability_id,
        models.CentreActivityAvailability.is_deleted == include_deleted
        ).first()
    
    if not db_centre_activity_availability:
        raise HTTPException(status_code=404, detail="Centre Activity Availability not found.")

    return db_centre_activity_availability

def get_centre_activity_availabilities(
        db: Session,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100    
    ):

    db_centre_activity_availabilities = db.query(models.CentreActivityAvailability).filter(models.CentreActivityAvailability.is_deleted == include_deleted)

    return (
        db_centre_activity_availabilities.order_by(models.CentreActivityAvailability.start_time.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_centre_activity_availability(
        db: Session,
        centre_activity_availability_data: schemas.CentreActivityAvailabilityUpdate,
        current_user_info: dict, 
    ):

    db_centre_activity_availability = (db.query(models.CentreActivityAvailability).filter(
        models.CentreActivityAvailability.id == centre_activity_availability_data.id,
        models.CentreActivityAvailability.is_deleted == False
        ).first())
    if not db_centre_activity_availability:
        raise HTTPException(status_code = 404, detail = "Centre Activity Availability not found.")

    original_data_dict = serialize_data(model_to_dict(db_centre_activity_availability))
    update_data_dict = serialize_data(centre_activity_availability_data.model_dump())

    modified_by_id = current_user_info.get("id") or centre_activity_availability_data.modified_by_id
    
    for field in schemas.CentreActivityAvailabilityUpdate.__fields__:
        if field != "Id" and hasattr(centre_activity_availability_data, field):
            setattr(db_centre_activity_availability, field, getattr(centre_activity_availability_data, field))
    db_centre_activity_availability.modified_by_id = modified_by_id
    db_centre_activity_availability.modified_date = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(db_centre_activity_availability)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail = f"Error updating Centre Activity Availability: {str(e)}")
    
    log_crud_action(
        action = ActionType.UPDATE,
        user = modified_by_id,
        user_full_name = current_user_info.get("fullname"),
        message = "Updated one record.",
        table = "CENTRE_ACTIVITY_AVAILABILITY",
        entity_id = db_centre_activity_availability.id,
        original_data = original_data_dict,
        updated_data = update_data_dict
    )
    return db_centre_activity_availability


def delete_centre_activity_availability(
        db: Session,
        centre_activity_availability_id: int,
        current_user_info: dict,
    ):

    db_centre_activity_availability = db.query(models.CentreActivityAvailability).filter(
        models.CentreActivityAvailability.id == centre_activity_availability_id,
        models.CentreActivityAvailability.is_deleted == False
        ).first()
    if not db_centre_activity_availability:
        raise HTTPException(status_code = 404, detail = "Centre Activity Availability not found.")
    
    db_centre_activity_availability.is_deleted = True
    db_centre_activity_availability.modified_by_id = current_user_info.get("id")
    db_centre_activity_availability.modified_date = datetime.now()

    try:
        db.commit()
        db.refresh(db_centre_activity_availability)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail = f"Error deleting Centre Activity Availability: {str(e)}")
    
    original_data_dict = serialize_data(model_to_dict(db_centre_activity_availability))

    log_crud_action(
        action = ActionType.DELETE,
        user = current_user_info.get("id"),
        user_full_name = current_user_info.get("fullname"),
        message = "Soft Deleted one record.",
        table = "CENTRE_ACTIVITY_AVAILABILITY",
        entity_id = db_centre_activity_availability.id,
        original_data = original_data_dict,
        updated_data = None
    )
    return db_centre_activity_availability
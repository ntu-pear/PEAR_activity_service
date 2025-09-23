from sqlalchemy.orm import Session
from sqlalchemy import extract
import app.models.centre_activity_availability_model as models
import app.schemas.centre_activity_availability_schema as schemas
import app.models.care_centre_model as care_centre_models
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.crud.care_centre_crud import get_care_centre_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

def _check_for_duplicate_availability(
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
                    "message": "Centre Activity Availability with these attributes exists or already soft deleted.",
                    "existing_id": str(existing_availability.id),
                    "existing_is_deleted": existing_availability.is_deleted
                })

def _check_centre_activity_availability_validity(
        db: Session,
        centre_activity_availability_data: schemas.CentreActivityAvailabilityCreate
    ):

    if centre_activity_availability_data.start_time.isoweekday() == 6 or centre_activity_availability_data.start_time.isoweekday() == 7:
        raise HTTPException(status_code=400,
                detail = {
                    "message": "Centre Activity Availability date cannot be on saturdays and sundays as the Care Centre is closed."
                })

    #This line of code must be changed when PEAR is scoped to handle multiple care centres.
    care_centre_info = get_care_centre_by_id(db, 1)

    day_of_the_week = centre_activity_availability_data.start_time.strftime('%A').lower()
    care_centre_working_hours = care_centre_info.working_hours[day_of_the_week]
    care_centre_opening_hours = datetime.strptime(care_centre_working_hours["open"], "%H:%M").time()
    care_centre_closing_hours = datetime.strptime(care_centre_working_hours["close"], "%H:%M").time()

    if centre_activity_availability_data.start_time.time() < care_centre_opening_hours or centre_activity_availability_data.end_time.time() > care_centre_closing_hours:
        raise HTTPException(status_code=400,
                detail = {
                    "message": "The selected Centre Activity Availability timing is outside of working hours. Care centre working hours on " 
                                + f"{day_of_the_week} is from {care_centre_opening_hours} to {care_centre_closing_hours}."
                })

    centre_activity = get_centre_activity_by_id(db, centre_activity_id=centre_activity_availability_data.centre_activity_id)
    if not centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found.")
    elif centre_activity:
        selected_availability_duration = (centre_activity_availability_data.end_time - centre_activity_availability_data.start_time).total_seconds() / 60

        if centre_activity.is_fixed and selected_availability_duration != centre_activity.min_duration and selected_availability_duration != centre_activity.max_duration:
            raise HTTPException(status_code=400,
                detail = {
                    "message": f"Centre Activity Availability selected duration must be the fixed duration of {centre_activity.max_duration} minutes."
                })
        #elif not centre_activity.is_fixed and selected_availability_duration < centre_activity.min_duration:
        #    raise HTTPException(status_code=400,
        #        detail = {
        #            "message": f"Centre Activity Availability selected duration cannot be less than the minimum duration of {centre_activity.min_duration} minutes."
        #        })

def create_centre_activity_availability(
        db:Session,
        centre_activity_availability_data: schemas.CentreActivityAvailabilityCreate,
        current_user_info: dict,
        is_recurring_everyday: bool = False
    ):
    list_db_centre_activity_availability = []
    current_user_id = current_user_info.get("id") or centre_activity_availability_data.created_by_id
    
    if not is_recurring_everyday:
        _check_for_duplicate_availability(db, centre_activity_availability_data)
        _check_centre_activity_availability_validity(db, centre_activity_availability_data)

        db_centre_activity_availability = models.CentreActivityAvailability(**centre_activity_availability_data.model_dump())
        db_centre_activity_availability.created_by_id = current_user_id
        db.add(db_centre_activity_availability)
        
    else:
        monday = centre_activity_availability_data.start_time - timedelta(days=centre_activity_availability_data.start_time.weekday())
        extracted_start_time = centre_activity_availability_data.start_time.time()
        extracted_end_time = centre_activity_availability_data.end_time.time()

        for i in range(5):
            db_centre_activity_availability = models.CentreActivityAvailability(**centre_activity_availability_data.model_dump())
            db_centre_activity_availability.created_by_id = current_user_id
            db_centre_activity_availability.start_time = datetime.combine(monday + timedelta(days=i), extracted_start_time)
            db_centre_activity_availability.end_time = datetime.combine(monday + timedelta(days=i), extracted_end_time)
            list_db_centre_activity_availability.append(db_centre_activity_availability)

        for item in list_db_centre_activity_availability:
            _check_for_duplicate_availability(db, item)
            _check_centre_activity_availability_validity(db, item)

        db.add_all(list_db_centre_activity_availability)

    try:
        db.commit()
        db.refresh(db_centre_activity_availability)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Centre Activity Availability: {str(e)}")
    
    if not is_recurring_everyday:
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
        list_db_centre_activity_availability.append(db_centre_activity_availability)
        return list_db_centre_activity_availability
    else:
        for record in list_db_centre_activity_availability:
            updated_data_dict = serialize_data(record)

            log_crud_action(
                action = ActionType.CREATE,
                user = current_user_id,
                user_full_name = current_user_info.get("fullname"),
                message = "Created a new record.",
                table = "CENTRE_ACTIVITY_AVAILABILITY",
                entity_id = record.id,
                original_data = None,
                updated_data = updated_data_dict
            )

        return list_db_centre_activity_availability

def get_centre_activity_availability_by_id(
        db: Session,
        centre_activity_availability_id: int,
        include_deleted: bool = False
    ):
    
    db_centre_activity_availability = db.query(models.CentreActivityAvailability)
    
    if not include_deleted:
        db_centre_activity_availability = db_centre_activity_availability.filter(models.CentreActivityAvailability.is_deleted == False)
        
    db_centre_activity_availability = db_centre_activity_availability.filter(
        models.CentreActivityAvailability.id == centre_activity_availability_id
    ).first()

    if not db_centre_activity_availability:
        raise HTTPException(status_code=404, detail="Centre Activity Availability not found or already soft deleted.")

    return db_centre_activity_availability

def get_centre_activity_availabilities(
        db: Session,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100    
    ) -> list[models.CentreActivityAvailability]:

    db_centre_activity_availabilities = db.query(models.CentreActivityAvailability)
   
    if not include_deleted:
        db_centre_activity_availabilities = db_centre_activity_availabilities.filter(models.CentreActivityAvailability.is_deleted == False)
    
    if not db_centre_activity_availabilities:
        raise HTTPException(status_code=404, detail="Centre Activity Availabilities cannot be found or already soft deleted.")

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
        raise HTTPException(status_code = 404, detail = "Centre Activity Availability not found or already soft deleted.")
    
    _check_for_duplicate_availability(db, centre_activity_availability_data)
    _check_centre_activity_availability_validity(db, centre_activity_availability_data)

    original_data = serialize_data(model_to_dict(db_centre_activity_availability))
    updated_data = serialize_data(centre_activity_availability_data.model_dump())

    modified_by_id = current_user_info.get("id") or centre_activity_availability_data.modified_by_id
    
    for field in schemas.CentreActivityAvailabilityUpdate.model_fields:
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
        original_data = original_data,
        updated_data = updated_data
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
        raise HTTPException(status_code = 404, detail = "Centre Activity Availability not found or already soft deleted.")
    
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
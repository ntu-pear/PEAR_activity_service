from sqlalchemy.orm import Session
from sqlalchemy import extract
import app.models.centre_activity_availability_model as models
import app.schemas.centre_activity_availability_schema as schemas
import app.models.care_centre_model as care_centre_models
from app.crud.centre_activity_crud import get_centre_activity_by_id
from app.crud.care_centre_crud import get_care_centre_by_id
from app.logger.logger_utils import log_crud_action, ActionType, serialize_data, model_to_dict
from app.services.outbox_service import get_outbox_service, generate_correlation_id
from fastapi import HTTPException
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Business fields compared to decide whether an update is worth publishing
_TRACKED_FIELDS = (
    "centre_activity_id", "days_of_week", "start_time", "end_time",
    "start_date", "end_date", "is_deleted",
)

def _availability_to_dict(obj) -> dict:
    """Columns only (no relationships), as JSON-serialisable values for messaging."""
    return serialize_data(model_to_dict(obj))

def _get_days_from_bitmask(days_of_week: int) -> list[str]:
    """
    Extract day names from bitmask.
    Bit 0 (value 1) = Monday
    Bit 1 (value 2) = Tuesday
    Bit 2 (value 4) = Wednesday
    Bit 3 (value 8) = Thursday
    Bit 4 (value 16) = Friday
    Bit 5 (value 32) = Saturday
    Bit 6 (value 64) = Sunday
    """
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    selected_days = []
    
    for i, day_name in enumerate(day_names):
        if days_of_week & (1 << i):
            selected_days.append(day_name)
    
    return selected_days

def _check_for_duplicate_availability(
        db:Session,
        centre_activity_availability_data: schemas.CentreActivityAvailabilityCreate,
        exclude_id: int = None
    ):
    
    conditions = [
        models.CentreActivityAvailability.centre_activity_id == centre_activity_availability_data.centre_activity_id,
        models.CentreActivityAvailability.start_time == centre_activity_availability_data.start_time,
        models.CentreActivityAvailability.end_time == centre_activity_availability_data.end_time,
        models.CentreActivityAvailability.days_of_week.op('&')(centre_activity_availability_data.days_of_week) != 0
    ]
    
    if centre_activity_availability_data.start_date is not None:
        conditions.append(models.CentreActivityAvailability.start_date == centre_activity_availability_data.start_date)
    if centre_activity_availability_data.end_date is not None:
        conditions.append(models.CentreActivityAvailability.end_date == centre_activity_availability_data.end_date)
    
    if exclude_id is not None:
        conditions.append(models.CentreActivityAvailability.id != exclude_id)
    
    existing_availability = db.query(models.CentreActivityAvailability).filter(*conditions).first()

    if existing_availability:
        raise HTTPException(status_code=400,
                detail = {
                    "message": "Centre Activity Availability conflicts with an existing record.",
                    "existing_id": str(existing_availability.id),
                    "existing_days_of_week": existing_availability.days_of_week,
                    "existing_is_deleted": existing_availability.is_deleted
                })

def _check_centre_activity_availability_validity(
        db: Session,
        centre_activity_availability_data: schemas.CentreActivityAvailabilityCreate
    ):


    #This line of code must be changed when PEAR is scoped to handle multiple care centres.
    care_centre_info = get_care_centre_by_id(db, 1)

    start_time = centre_activity_availability_data.start_time.replace(tzinfo=None)
    end_time = centre_activity_availability_data.end_time.replace(tzinfo=None)


    selected_days = _get_days_from_bitmask(centre_activity_availability_data.days_of_week)
    for day_of_the_week in selected_days:
        working_hours = care_centre_info.working_hours.get(day_of_the_week)

        if not working_hours["open"] or not working_hours["close"]:
            raise HTTPException(status_code=400,
                detail = {
                    "message": f"The selected Centre Activity Availability timing is outside of working hours. Care centre is closed on {day_of_the_week}."
                })
        
        opening_hours = datetime.strptime(working_hours["open"], "%H:%M").time()
        closing_hours = datetime.strptime(working_hours["close"], "%H:%M").time()
        if start_time < opening_hours or end_time > closing_hours:
            raise HTTPException(status_code=400,
                detail = {
                    "message": "The selected Centre Activity Availability timing is outside of working hours. Care centre working hours on " 
                                + f"{day_of_the_week} is from {opening_hours} to {closing_hours}."
                })

    centre_activity = get_centre_activity_by_id(db, centre_activity_id=centre_activity_availability_data.centre_activity_id)
    if not centre_activity:
        raise HTTPException(status_code=404, detail="Centre Activity not found.")
    elif centre_activity:
        start_dt = datetime.combine(datetime.today(), start_time)
        end_dt = datetime.combine(datetime.today(), end_time)
        selected_availability_duration = (end_dt - start_dt).total_seconds() / 60

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
        correlation_id: str = None,
    ):
    current_user_id = current_user_info.get("id") or centre_activity_availability_data.created_by_id

    _check_for_duplicate_availability(db, centre_activity_availability_data)
    _check_centre_activity_availability_validity(db, centre_activity_availability_data)

    if not correlation_id:
        correlation_id = generate_correlation_id()

    centre_activity = get_centre_activity_by_id(db, centre_activity_availability_data.centre_activity_id)
    activity_name = centre_activity.activity.title if centre_activity and centre_activity.activity else "Unknown"

    try:
        timestamp = datetime.now()
        db_centre_activity_availability = models.CentreActivityAvailability(**centre_activity_availability_data.model_dump())
        db_centre_activity_availability.created_by_id = current_user_id
        db_centre_activity_availability.created_date = timestamp
        db.add(db_centre_activity_availability)
        db.flush()  # assign the primary key without committing

        # Emit the domain event in the same transaction (outbox pattern)
        event_payload = {
            "event_type": "CENTRE_ACTIVITY_AVAILABILITY_CREATED",
            "availability_id": db_centre_activity_availability.id,
            "availability_data": _availability_to_dict(db_centre_activity_availability),
            "created_by": current_user_id,
            "created_by_name": current_user_info.get("fullname"),
            "timestamp": timestamp.isoformat(),
            "correlation_id": correlation_id,
        }
        outbox_event = get_outbox_service().create_event(
            db=db,
            event_type="CENTRE_ACTIVITY_AVAILABILITY_CREATED",
            aggregate_id=db_centre_activity_availability.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity_availability.created.{db_centre_activity_availability.id}",
            correlation_id=correlation_id,
            created_by=current_user_id,
        )

        log_crud_action(
            action = ActionType.CREATE,
            user = current_user_id,
            user_full_name = current_user_info.get("fullname"),
            message = f"Created centre activity availability: {activity_name}",
            table = "CENTRE_ACTIVITY_AVAILABILITY",
            entity_id = db_centre_activity_availability.id,
            original_data = None,
            updated_data = serialize_data(centre_activity_availability_data.model_dump()),
            log_type= "system",
            is_system_config= True,
        )

        db.commit()
        db.refresh(db_centre_activity_availability)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create centre activity availability: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating Centre Activity Availability: {str(e)}") from e

    logger.info(
        f"Created centre activity availability {db_centre_activity_availability.id} with outbox event "
        f"{outbox_event.id} (correlation: {correlation_id})"
    )
    return db_centre_activity_availability

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
        correlation_id: str = None,
    ):

    db_centre_activity_availability = (db.query(models.CentreActivityAvailability).filter(
        models.CentreActivityAvailability.id == centre_activity_availability_data.id
        ).first())
    if not db_centre_activity_availability:
        raise HTTPException(status_code = 404, detail = "Centre Activity Availability not found.")

    _check_for_duplicate_availability(db, centre_activity_availability_data, exclude_id=centre_activity_availability_data.id)
    _check_centre_activity_availability_validity(db, centre_activity_availability_data)

    if not correlation_id:
        correlation_id = generate_correlation_id()

    original_data = serialize_data(model_to_dict(db_centre_activity_availability))
    updated_data = serialize_data(centre_activity_availability_data.model_dump())

    # Only business field changes are published; audit-only saves are not
    changes = {}
    for field in _TRACKED_FIELDS:
        old_value = getattr(db_centre_activity_availability, field)
        new_value = getattr(centre_activity_availability_data, field)
        if old_value != new_value:
            changes[field] = {"old": serialize_data(old_value), "new": serialize_data(new_value)}

    modified_by_id = current_user_info.get("id") or centre_activity_availability_data.modified_by_id

    try:
        for field in schemas.CentreActivityAvailabilityUpdate.model_fields.keys():
            if field != "id" and hasattr(centre_activity_availability_data, field):
                setattr(db_centre_activity_availability, field, getattr(centre_activity_availability_data, field))
        db_centre_activity_availability.modified_by_id = modified_by_id
        db_centre_activity_availability.modified_date = datetime.now(timezone.utc)
        db.flush()

        outbox_event = None
        if changes:
            event_payload = {
                "event_type": "CENTRE_ACTIVITY_AVAILABILITY_UPDATED",
                "availability_id": db_centre_activity_availability.id,
                "old_data": original_data,
                "new_data": _availability_to_dict(db_centre_activity_availability),
                "changes": changes,
                "modified_by": modified_by_id,
                "modified_by_name": current_user_info.get("fullname"),
                "timestamp": datetime.now().isoformat(),
                "correlation_id": correlation_id,
            }
            outbox_event = get_outbox_service().create_event(
                db=db,
                event_type="CENTRE_ACTIVITY_AVAILABILITY_UPDATED",
                aggregate_id=db_centre_activity_availability.id,
                payload=event_payload,
                routing_key=f"activity.centre_activity_availability.updated.{db_centre_activity_availability.id}",
                correlation_id=correlation_id,
                created_by=modified_by_id,
            )

        centre_activity = db_centre_activity_availability.centre_activity
        activity_name = centre_activity.activity.title if centre_activity and centre_activity.activity else "Unknown"

        log_crud_action(
            action = ActionType.UPDATE,
            user = modified_by_id,
            user_full_name = current_user_info.get("fullname"),
            message = f"Updated centre activity availability: {activity_name}.",
            table = "CENTRE_ACTIVITY_AVAILABILITY",
            entity_id = db_centre_activity_availability.id,
            original_data = original_data,
            updated_data = updated_data,
            log_type= "system",
            is_system_config= True,
        )

        db.commit()
        db.refresh(db_centre_activity_availability)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update centre activity availability: {str(e)}")
        raise HTTPException(status_code = 500, detail = f"Error updating Centre Activity Availability: {str(e)}") from e

    if outbox_event is not None:
        logger.info(
            f"Updated centre activity availability {db_centre_activity_availability.id} with outbox event "
            f"{outbox_event.id} (correlation: {correlation_id})"
        )
    else:
        logger.info(f"Updated centre activity availability {db_centre_activity_availability.id} with no business changes")
    return db_centre_activity_availability

def delete_centre_activity_availability(
        db: Session,
        centre_activity_availability_id: int,
        current_user_info: dict,
        correlation_id: str = None,
    ):

    db_centre_activity_availability = db.query(models.CentreActivityAvailability).filter(
        models.CentreActivityAvailability.id == centre_activity_availability_id,
        models.CentreActivityAvailability.is_deleted == False
        ).first()
    if not db_centre_activity_availability:
        raise HTTPException(status_code = 404, detail = "Centre Activity Availability not found or already soft deleted.")

    if not correlation_id:
        correlation_id = generate_correlation_id()

    # Captured before the soft delete, matching the other entities' DELETED payloads
    availability_data = _availability_to_dict(db_centre_activity_availability)

    try:
        timestamp = datetime.now()
        db_centre_activity_availability.is_deleted = True
        db_centre_activity_availability.modified_by_id = current_user_info.get("id")
        db_centre_activity_availability.modified_date = timestamp
        db.flush()

        event_payload = {
            "event_type": "CENTRE_ACTIVITY_AVAILABILITY_DELETED",
            "availability_id": db_centre_activity_availability.id,
            "availability_data": availability_data,
            "deleted_by": current_user_info.get("id"),
            "deleted_by_name": current_user_info.get("fullname"),
            "timestamp": timestamp.isoformat(),
            "correlation_id": correlation_id,
        }
        outbox_event = get_outbox_service().create_event(
            db=db,
            event_type="CENTRE_ACTIVITY_AVAILABILITY_DELETED",
            aggregate_id=db_centre_activity_availability.id,
            payload=event_payload,
            routing_key=f"activity.centre_activity_availability.deleted.{db_centre_activity_availability.id}",
            correlation_id=correlation_id,
            created_by=current_user_info.get("id"),
        )

        centre_activity = db_centre_activity_availability.centre_activity
        activity_name = centre_activity.activity.title if centre_activity and centre_activity.activity else "Unknown"

        log_crud_action(
            action = ActionType.DELETE,
            user = current_user_info.get("id"),
            user_full_name = current_user_info.get("fullname"),
            message = f"Deleted centre activity availability: {activity_name}.",
            table = "CENTRE_ACTIVITY_AVAILABILITY",
            entity_id = db_centre_activity_availability.id,
            original_data = serialize_data(model_to_dict(db_centre_activity_availability)),
            updated_data = None,
            log_type= "system",
            is_system_config= True,
        )

        db.commit()
        db.refresh(db_centre_activity_availability)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete centre activity availability: {str(e)}")
        raise HTTPException(status_code = 500, detail = f"Error deleting Centre Activity Availability: {str(e)}") from e

    logger.info(
        f"Deleted centre activity availability {db_centre_activity_availability.id} with outbox event "
        f"{outbox_event.id} (correlation: {correlation_id})"
    )
    return db_centre_activity_availability

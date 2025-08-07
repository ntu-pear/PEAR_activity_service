from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.centre_activity_availability_crud as crud 
import app.schemas.centre_activity_availability_schema as schemas
from app.auth.jwt_utils import get_current_user_with_flag, JWTPayload, is_supervisor
from typing import Optional

router = APIRouter()

@router.post(
    "/",
    response_model = schemas.CentreActivityAvailabilityResponse,
    summary = "Create Centre Activity Availability",
    description = "Create a Centre Activity Availability record.",
    status_code = status.HTTP_201_CREATED
)

def create_centre_activity_availability(
    payload: schemas.CentreActivityAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You do not have permission to create a Centre Activity Availability."
        )
    
    current_user_info = grab_user_info(current_user)

    return crud.create_centre_activity_availability(
        db = db,
        centre_activity_availability_data = payload,
        current_user_info = current_user_info
    )


@router.get(
    "/",
    summary = "List Centre Activity Availabilities",
    description = "Get all Centre Activity Availability records",
    response_model = list[schemas.CentreActivityAvailabilityResponse]
)

def get_all_centre_activity_availabilities(
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    include_deleted: bool = Query(False, description = "Include soft-deleted records.")
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You do not have permission to view Centre Activity Availabilities."
        )
    
    return crud.get_centre_activity_availabilities(db, include_deleted = include_deleted)


@router.get(
    "/{centre_activity_availability_id}",
    summary = "Get Centre Activity Availability by ID",
    description = "Get a specific Centre Activity Availability record by its ID.",
    response_model = schemas.CentreActivityAvailabilityResponse
)

def get_centre_activity_availability_by_id(
    centre_activity_availability_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    include_deleted: bool = Query(False, description = "Include soft-deleted records.")
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You do not have permission to view a Centre Activity Availability."
        )
    
    return crud.get_centre_activity_availability_by_id(db, centre_activity_availability_id, include_deleted = include_deleted)


@router.put(
    "/",
    summary = "Update Centre Activity Availability",
    description = "Update an existing Centre Activity Availability record that is not soft deleted.",
    response_model = schemas.CentreActivityAvailabilityResponse
)

def update_centre_activity_availability(
    centre_activity_availability: schemas.CentreActivityAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You do not have permission to update a Centre Activity Availability."
        )
    
    current_user_info = grab_user_info(current_user)

    return crud.update_centre_activity_availability(
        db = db,
        centre_activity_availability_data = centre_activity_availability,
        current_user_info = current_user_info
    )


@router.delete(
    "/{centre_activity_availability_id}",
    summary = "Delete Centre Activity Availability by ID",
    description = "Delete a specific Centre Activity Availability record by its ID.",
    response_model = schemas.CentreActivityAvailabilityResponse
)

def delete_centre_activity_availability(
    centre_activity_availability_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag)
):
    
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You do not have permission to delete a Centre Activity Availability."
        )
    
    current_user_info = grab_user_info(current_user)

    return crud.delete_centre_activity_availability(
        db = db,
        centre_activity_availability_id =centre_activity_availability_id,
        current_user_info = current_user_info
    )

def grab_user_info(user_info: JWTPayload):
    extracted_user_info = {
        "id": user_info.userId if user_info else None,
        "fullname": user_info.fullName if user_info else "Anonymous"
    }
    return extracted_user_info
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.care_centre_crud as crud 
import app.schemas.care_centre_schema as schemas
from app.auth.jwt_utils import get_current_user_with_flag, JWTPayload, is_supervisor
from typing import Optional

router = APIRouter()

@router.post(
        "/", 
        response_model=schemas.CareCentreResponse, 
        summary="Create Care Centre",
        description="Create a new Care Centre", 
        status_code=status.HTTP_201_CREATED)
def create_care_centre(
    payload: schemas.CareCentreCreate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a Care Centre."
        )
    
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }
    return crud.create_care_centre(
        db=db,
        care_centre_data=payload,
        current_user_info=current_user_info,
    )

@router.get(
        "/",
        summary="List Care Centres",
        description="List all Care Centres",
        response_model=list[schemas.CareCentreResponse])
def list_care_centres(
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view Care Centres."
        )
    return crud.get_care_centres(db, skip=skip, limit=limit, include_deleted=include_deleted)

@router.get(
        "/{care_centre_id}",
        summary="Get Care Centre by ID",
        description="Get a specific Care Centre by its ID",
        response_model=schemas.CareCentreResponse)
def get_care_centre_by_id(
    care_centre_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    include_deleted: bool = False,
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this Care Centre."
        )
    
    care_centre = crud.get_care_centre_by_id(db, care_centre_id, include_deleted=include_deleted)
    return care_centre

@router.put(
        "/",
        summary="Update Care Centre",
        description="Update an existing Care Centre",
        response_model=schemas.CareCentreResponse)
def update_care_centre(
    payload: schemas.CareCentreUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update a Care Centre."
        )
    
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }
    return crud.update_care_centre(
        db=db,
        care_centre_data=payload,
        current_user_info=current_user_info,
    )

@router.delete(
        "/{care_centre_id}",
        summary="Delete Care Centre",
        description="Delete a Care Centre by its ID",
        response_model=schemas.CareCentreResponse)
def delete_care_centre(
    care_centre_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete a Care Centre."
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }
    return crud.delete_care_centre(
        db=db,
        care_centre_id=care_centre_id,
        current_user_info=current_user_info,
    )
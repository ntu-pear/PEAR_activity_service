from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.routine_exclusion_crud as crud
import app.schemas.routine_exclusion_schema as schemas
from app.auth.jwt_utils import get_user_and_token, get_current_user, JWTPayload, is_supervisor
from typing import Optional, Tuple

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.RoutineExclusionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a routine exclusion"
)
def create_routine_exclusion(
    exclusion: schemas.RoutineExclusionCreate,
    db: Session = Depends(get_db),
    user_and_token: Tuple[Optional[JWTPayload], Optional[str]] = Depends(get_user_and_token),
):
    current_user, token = user_and_token
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a routine exclusion."
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
        "bearer_token": token
    }
    return crud.create_routine_exclusion(db=db, exclusion_data=exclusion, current_user_info=current_user_info)

@router.get(
    "/",
    response_model=list[schemas.RoutineExclusionResponse],
    summary="List all routine exclusions"
)
def list_routine_exclusions(
    include_deleted: bool = Query(False, description="Include soft-deleted exclusions"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view routine exclusions."
        )
    return crud.get_routine_exclusions(
        db=db,
        include_deleted=include_deleted,
        skip=skip,
        limit=limit
    )

@router.get(
    "/{exclusion_id}",
    response_model=schemas.RoutineExclusionResponse,
    summary="Get routine exclusion by ID"
)
def get_routine_exclusion_by_id(
    exclusion_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view routine exclusions."
        )
    return crud.get_routine_exclusion_by_id(
        db=db,
        exclusion_id=exclusion_id,
        include_deleted=include_deleted
    )

@router.get(
    "/patient/{patient_id}",
    response_model=list[schemas.RoutineExclusionResponse],
    summary="List routine exclusions by patient"
)
def list_routine_exclusions_by_patient(
    patient_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view routine exclusions."
        )
    return crud.get_routine_exclusions_by_patient_id(db, patient_id, include_deleted)

@router.get(
    "/routine/{routine_id}",
    response_model=list[schemas.RoutineExclusionResponse],
    summary="List routine exclusions by routine"
)
def list_routine_exclusions_by_routine(
    routine_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view routine exclusions."
        )
    return crud.get_routine_exclusions_by_routine_id(db, routine_id, include_deleted)

@router.put(
    "/",
    response_model=schemas.RoutineExclusionResponse,
    summary="Update routine exclusion"
)
def update_routine_exclusion(
    exclusion: schemas.RoutineExclusionUpdate,
    db: Session = Depends(get_db),
    user_and_token: Tuple[Optional[JWTPayload], Optional[str]] = Depends(get_user_and_token),
):
    current_user, token = user_and_token
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update routine exclusions."
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
        "bearer_token": token
    }
    return crud.update_routine_exclusion(db=db, exclusion_data=exclusion, current_user_info=current_user_info)

@router.delete(
    "/{exclusion_id}",
    response_model=schemas.RoutineExclusionResponse,
    summary="Delete routine exclusion"
)
def delete_routine_exclusion(
    exclusion_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete routine exclusions."
        )
    user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous"
    }
    return crud.delete_routine_exclusion(db=db, exclusion_id=exclusion_id, current_user_info=user_info)

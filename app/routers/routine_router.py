from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.routine_crud as crud
import app.schemas.routine_schema as schemas
from app.auth.jwt_utils import get_user_and_token, get_current_user, JWTPayload, is_supervisor
from typing import Optional, Tuple

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.RoutineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a routine"
)
def create_routine(
    routine: schemas.RoutineCreate,
    db: Session = Depends(get_db),
    user_and_token: Tuple[Optional[JWTPayload], Optional[str]] = Depends(get_user_and_token),
):
    current_user, token = user_and_token
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a routine."
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
        "bearer_token": token
    }
    return crud.create_routine(db=db, routine_data=routine, current_user_info=current_user_info)

@router.get(
    "/",
    response_model=list[schemas.RoutineResponse],
    summary="List all routines"
)
def list_routines(
    include_deleted: bool = Query(False, description="Include soft-deleted routines"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view routines."
        )
    return crud.get_routines(
        db=db,
        include_deleted=include_deleted,
        skip=skip,
        limit=limit
    )

@router.get(
    "/{routine_id}",
    response_model=schemas.RoutineResponse,
    summary="Get routine by ID"
)
def get_routine_by_id(
    routine_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view routines."
        )
    return crud.get_routine_by_id(
        db=db,
        routine_id=routine_id,
        include_deleted=include_deleted
    )

@router.get(
    "/patient/{patient_id}",
    response_model=list[schemas.RoutineResponse],
    summary="List routines by patient"
)
def list_routines_by_patient(
    patient_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view routines."
        )
    return crud.get_routines_by_patient_id(db, patient_id, include_deleted)

@router.put(
    "/",
    response_model=schemas.RoutineResponse,
    summary="Update routine"
)
def update_routine(
    routine: schemas.RoutineUpdate,
    db: Session = Depends(get_db),
    user_and_token: Tuple[Optional[JWTPayload], Optional[str]] = Depends(get_user_and_token),
):
    current_user, token = user_and_token
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update routines."
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
        "bearer_token": token
    }
    return crud.update_routine(db=db, routine_data=routine, current_user_info=current_user_info)

@router.delete(
    "/{routine_id}",
    response_model=schemas.RoutineResponse,
    summary="Delete routine"
)
def delete_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete routines."
        )
    user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous"
    }
    return crud.delete_routine(db=db, routine_id=routine_id, current_user_info=user_info)

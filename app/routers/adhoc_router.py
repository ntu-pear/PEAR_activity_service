from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.adhoc_crud as crud
import app.schemas.adhoc_schema as schemas
from app.auth.jwt_utils import get_user_and_token, get_current_user, JWTPayload, is_supervisor
from typing import List, Optional, Tuple

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.AdhocResponse,
    status_code=status.HTTP_201_CREATED
)
def create_adhoc(
    adhoc: schemas.AdhocCreate,
    db: Session = Depends(get_db),
    user_and_token: Tuple[Optional[JWTPayload], Optional[str]] = Depends(get_user_and_token),
):
    current_user, token = user_and_token
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create an Adhoc record."
        )
    current_user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
        "bearer_token": token
    }
    return crud.create_adhoc(db=db, adhoc_data=adhoc, current_user_info=current_user_info)

@router.get(
    "/",
    response_model=list[schemas.AdhocResponse],
    summary="List Adhoc records",
    description="List adhoc activity replacement records (supervisor only)"
)
def list_adhocs(
    include_deleted: bool = Query(False, description="Include soft‑deleted"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view Adhoc records."
        )
    return crud.get_adhocs(
        db=db,
        include_deleted=include_deleted,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{adhoc_id}",
    response_model=schemas.AdhocResponse,
    summary="Get Adhoc by ID",
    description="Retrieve a single adhoc record by its ID"
)
def get_adhoc_by_id(
    adhoc_id: int,
    include_deleted: bool = Query(False, description="Include soft‑deleted"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view Adhoc records."
        )
    return crud.get_adhoc_by_id(
        db=db,
        adhoc_id=adhoc_id,
        include_deleted=include_deleted
    )

@router.get(
    "/patient/{patient_id}",
    response_model=List[schemas.AdhocResponse],
    summary="List Adhoc by patient"
)
def list_adhocs_by_patient(
    patient_id: int,
    include_deleted: bool = Query(False, description="Include soft‑deleted"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to retrieve Adhoc records from patient."
        )
    return crud.get_adhocs_by_patient_id(db, patient_id, include_deleted)

@router.put(
    "/",
    response_model=schemas.AdhocResponse,
    summary="Update Adhoc record",
    description="Modify an existing adhoc record (supervisor only)"
)
def update_adhoc(
    adhoc: schemas.AdhocUpdate,
    db: Session = Depends(get_db),
    user_and_token: Tuple[Optional[JWTPayload], Optional[str]] = Depends(get_user_and_token),
):
    current_user, token = user_and_token
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update Adhoc records."
        )
    current_user_info  = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
        "bearer_token": token
    } 
    return crud.update_adhoc(db=db, adhoc_data=adhoc, current_user_info=current_user_info)

@router.delete(
    "/{adhoc_id}",
    response_model=schemas.AdhocResponse,
    summary="Delete Adhoc",
    description="Soft‑delete an adhoc record (supervisor only)"
)
def delete_adhoc(
    adhoc_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user)
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete Adhoc records."
        )
    user_info = {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous"
    }
    return crud.delete_adhoc(db=db, adhoc_id=adhoc_id, current_user_info=user_info)
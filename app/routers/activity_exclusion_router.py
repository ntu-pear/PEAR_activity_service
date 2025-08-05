from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session

import app.crud.activity_exclusion_crud as crud
import app.schemas.activity_exclusion_schema as schemas
from app.database import get_db
from app.auth.jwt_utils import get_current_user_with_flag, JWTPayload, is_supervisor

router = APIRouter()

@router.post("/", response_model=schemas.ActivityExclusionResponse, status_code=status.HTTP_201_CREATED)
def create_exclusion(
    payload: schemas.ActivityExclusionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only Supervisors may create exclusions")
    user_info = {"id": current_user.userId if current_user else None, "fullname": current_user.fullName if current_user else "Anonymous"}
    return crud.create_exclusion(db, payload, user_info)

@router.get("/", response_model=List[schemas.ActivityExclusionResponse])
def list_exclusions(
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
    include_deleted: bool = Query(False, description="Include soft-deleted?"),
    skip: int = Query(0, ge=0, description="Skip this many"),
    limit: int = Query(100, gt=0, le=1000, description="Max to return"),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only Supervisors may view exclusions")
    return crud.get_exclusions(db, include_deleted, skip, limit)

@router.get("/{exclusion_id}", response_model=schemas.ActivityExclusionResponse)
def get_exclusion(
    exclusion_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only Supervisors may view exclusions")
    return crud.get_exclusion_by_id(db, exclusion_id)

@router.put("/", response_model=schemas.ActivityExclusionResponse)
def update_exclusion(
    payload: schemas.ActivityExclusionUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only Supervisors may update exclusions")
    user_info = {"id": current_user.userId if current_user else None, "fullname": current_user.fullName if current_user else "Anonymous"}
    return crud.update_exclusion(db, payload, user_info)

@router.delete("/{exclusion_id}", response_model=schemas.ActivityExclusionResponse)
def delete_exclusion(
    exclusion_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user_with_flag),
):
    if current_user and not is_supervisor(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only Supervisors may delete exclusions")
    user_info = {"id": current_user.userId if current_user else None, "fullname": current_user.fullName if current_user else "Anonymous"}
    return crud.delete_exclusion(db, exclusion_id, user_info)
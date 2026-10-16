from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import app.crud.activity_template_crud as crud
import app.crud.apply_template_crud as apply_crud
import app.schemas.activity_template_schema as schemas
import app.schemas.apply_template_schema as apply_schemas
from app.auth.jwt_utils import JWTPayload, get_current_user, is_admin, is_supervisor
from app.database import get_db

router = APIRouter()

# Creating an activity through a template must not be an easier path than
# creating one directly, so these match what centre activities require.
PERMISSION_DENIED = "You do not have permission to manage Activity Templates."


def _require_supervisor_or_admin(current_user: Optional[JWTPayload]):
    if not (is_supervisor(current_user) or is_admin(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=PERMISSION_DENIED
        )


def _user_info(current_user: Optional[JWTPayload]) -> dict:
    return {
        "id": current_user.userId if current_user else None,
        "fullname": current_user.fullName if current_user else "Anonymous",
    }


@router.post(
    "/",
    response_model=schemas.ActivityTemplateResponse,
    summary="Create Activity Template",
    description="Save a blank activity form for reuse. Creates no activity and publishes no event.",
    status_code=status.HTTP_201_CREATED,
)
def create_activity_template(
    payload: schemas.ActivityTemplateCreate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
):
    _require_supervisor_or_admin(current_user)
    return crud.create_activity_template(
        db=db, template_data=payload, current_user_info=_user_info(current_user)
    )


@router.get(
    "/",
    response_model=List[schemas.ActivityTemplateResponse],
    summary="List Activity Templates",
    description="List saved standard templates, for the picker.",
)
def get_activity_templates(
    include_deleted: bool = Query(False, description="Include soft-deleted templates"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
):
    return crud.get_activity_templates(
        db=db, include_deleted=include_deleted, skip=skip, limit=limit
    )


@router.get(
    "/{template_id}",
    response_model=schemas.ActivityTemplateResponse,
    summary="Get Activity Template",
    description="One template, for pre-filling the form.",
)
def get_activity_template(
    template_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted templates"),
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
):
    return crud.get_activity_template_by_id(
        db=db, template_id=template_id, include_deleted=include_deleted
    )


@router.put(
    "/",
    response_model=schemas.ActivityTemplateResponse,
    summary="Update Activity Template",
    description="Edit a stored template. Does not affect activities already created from it.",
)
def update_activity_template(
    payload: schemas.ActivityTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
):
    _require_supervisor_or_admin(current_user)
    return crud.update_activity_template(
        db=db, template_data=payload, current_user_info=_user_info(current_user)
    )


@router.delete(
    "/{template_id}",
    response_model=schemas.ActivityTemplateResponse,
    summary="Delete Activity Template",
    description="Soft-delete a template. Activities already created from it are unaffected.",
)
def delete_activity_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
):
    _require_supervisor_or_admin(current_user)
    return crud.delete_activity_template(
        db=db, template_id=template_id, current_user_info=_user_info(current_user)
    )


@router.post(
    "/{template_id}/apply",
    response_model=apply_schemas.ApplyTemplateResponse,
    summary="Apply Activity Template",
    description=(
        "Create an Activity and a Centre Activity from the submitted values, in one "
        "transaction. Reuses an existing active Activity when one already has this "
        "title, so the same template can be applied more than once - producing, say, "
        "'Breathing AM' and 'Breathing PM' under a single 'Breathing' activity. "
        "The stored template is not modified."
    ),
    status_code=status.HTTP_201_CREATED,
)
def apply_activity_template(
    template_id: int,
    payload: apply_schemas.ApplyTemplateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[JWTPayload] = Depends(get_current_user),
):
    _require_supervisor_or_admin(current_user)
    activity, centre_activity, activity_was_created = apply_crud.apply_activity_template(
        db=db,
        template_id=template_id,
        payload=payload,
        current_user_info=_user_info(current_user),
    )
    return apply_schemas.ApplyTemplateResponse(
        activity_id=activity.id,
        activity_title=activity.title,
        activity_was_created=activity_was_created,
        centre_activity_id=centre_activity.id,
        centre_activity_name=centre_activity.name,
    )

"""Applying an activity template.

Stage two of the supervisor's flow. They open a saved standard template, name the
centre activity it should produce, adjust anything else and submit. This is what
creates activity data; saving the template itself created nothing.

Two things here are load-bearing and easy to get wrong:

1. The activity is get-or-create, not create. Applying "Breathing" twice must
   produce one Activity with two Centre Activities under it, not two Activities -
   which the duplicate-title guard would reject anyway.

2. The two events carry distinct correlation identifiers. The scheduler's
   consumer discards a correlation id it has already processed, so sharing one
   across both events means the second is silently dropped. That is the defect
   that cost ten months of drift on the cascade path, and this is the next place
   in the system with the same shape.
"""
import logging
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.models.activity_model as activity_models
import app.schemas.activity_schema as activity_schemas
import app.schemas.centre_activity_schema as centre_activity_schemas
from app.crud.activity_crud import create_activity
from app.crud.activity_template_crud import get_activity_template_by_id
from app.crud.centre_activity_crud import create_centre_activity
from app.schemas.apply_template_schema import ApplyTemplateRequest
from app.services.outbox_service import generate_correlation_id

logger = logging.getLogger(__name__)


def _find_active_activity_by_title(db: Session, title: str) -> Optional[activity_models.Activity]:
    return (
        db.query(activity_models.Activity)
          .filter(
              activity_models.Activity.title == title,
              activity_models.Activity.is_deleted == False,
          )
          .first()
    )


def apply_activity_template(
    db: Session,
    *,
    template_id: int,
    payload: ApplyTemplateRequest,
    current_user_info: dict,
) -> Tuple[activity_models.Activity, object, bool]:
    """Create the Activity and Centre Activity a template describes.

    Returns (activity, centre_activity, activity_was_created).

    Everything commits together or not at all. A half-applied template would
    leave an activity nobody can schedule, with nothing to retry it.
    """
    # Rejects an apply against a deleted template, and gives the audit log
    # something to record the template by.
    template = get_activity_template_by_id(db, template_id=template_id)

    current_user_id = current_user_info.get("id")

    existing_activity = _find_active_activity_by_title(db, payload.title)
    activity_was_created = existing_activity is None

    try:
        if existing_activity is not None:
            # Reuse it untouched. No update, so no activity event - nothing about
            # the activity changed, only that another configuration now points at
            # it. This is what lets one template produce Breathing AM and
            # Breathing PM under a single activity.
            activity = existing_activity
            logger.info(
                f"Applying template {template_id}: reusing activity {activity.id} "
                f"titled {payload.title!r}"
            )
        else:
            activity = create_activity(
                db=db,
                activity_in=activity_schemas.ActivityCreate(
                    title=payload.title,
                    description=payload.description,
                ),
                current_user_info=current_user_info,
                correlation_id=generate_correlation_id(),
                commit=False,
            )
            logger.info(
                f"Applying template {template_id}: created activity {activity.id} "
                f"titled {payload.title!r}"
            )

        centre_activity = create_centre_activity(
            db=db,
            centre_activity_data=centre_activity_schemas.CentreActivityCreate(
                activity_id=activity.id,
                name=payload.name,
                care_centre_id=payload.care_centre_id,
                is_compulsory=payload.is_compulsory,
                is_fixed=payload.is_fixed,
                is_group=payload.is_group,
                start_date=payload.start_date,
                end_date=payload.end_date,
                min_duration=payload.min_duration,
                max_duration=payload.max_duration,
                min_people_req=payload.min_people_req,
                fixed_time_slots=payload.fixed_time_slots,
                created_by_id=current_user_id,
            ),
            current_user_info=current_user_info,
            # Its own identifier, never the one the activity event used.
            correlation_id=generate_correlation_id(),
            commit=False,
        )

        db.commit()
        db.refresh(activity)
        db.refresh(centre_activity)

    except HTTPException:
        # Validation failures from either create carry their own status and
        # message, which are more useful than a generic 500.
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to apply template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying Activity Template: {str(e)}",
        )

    logger.info(
        f"Applied template {template_id}: activity {activity.id} "
        f"({'created' if activity_was_created else 'reused'}), "
        f"centre activity {centre_activity.id} named {payload.name!r}"
    )
    return activity, centre_activity, activity_was_created

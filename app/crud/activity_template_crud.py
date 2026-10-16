"""CRUD for Activity Templates.

Deliberately boring. A template is a stored form: saving one writes a row and
nothing else. There is no outbox event, no routing key and no consumer, because
the Scheduler has no concept of a template. Applying a template is what creates
activity data, and that lives in the apply endpoint rather than here.
"""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.models.activity_template_model as models
import app.schemas.activity_template_schema as schemas
from app.logger.change_summary import with_change_summary
from app.logger.logger_utils import ActionType, log_crud_action, serialize_data
from app.models.care_centre_model import CareCentre


def _validate_care_centre_exists(db: Session, care_centre_id: Optional[int]):
    """Validate the default care centre exists, when one was supplied."""
    if care_centre_id is None:
        return
    care_centre = (
        db.query(CareCentre)
          .filter(CareCentre.id == care_centre_id, CareCentre.is_deleted == False)
          .first()
    )
    if not care_centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Care Centre not found")


def _validate_name_unique(db: Session, name: str, exclude_id: Optional[int] = None):
    """Template names identify templates in the picker, so they must be distinct.

    Only among active templates: a name freed by a deletion can be reused.
    """
    query = db.query(models.ActivityTemplate).filter(
        models.ActivityTemplate.name == name,
        models.ActivityTemplate.is_deleted == False,
    )
    if exclude_id is not None:
        query = query.filter(models.ActivityTemplate.id != exclude_id)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activity Template with this name already exists",
        )


def create_activity_template(
    db: Session,
    template_data: schemas.ActivityTemplateCreate,
    current_user_info: dict,
) -> models.ActivityTemplate:
    _validate_name_unique(db, template_data.name)
    _validate_care_centre_exists(db, template_data.care_centre_id)

    current_user_id = current_user_info.get("id") or template_data.created_by_id
    db_template = models.ActivityTemplate(**template_data.model_dump())
    db_template.created_by_id = current_user_id

    db.add(db_template)
    try:
        db.commit()
        db.refresh(db_template)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Activity Template: {str(e)}")

    log_crud_action(
        action=ActionType.CREATE,
        user=current_user_id,
        user_full_name=current_user_info.get("fullname"),
        message=f"Created Activity Template: {db_template.name}",
        table="ACTIVITY_TEMPLATE",
        entity_id=db_template.id,
        original_data=None,
        updated_data=serialize_data(template_data.model_dump()),
        log_type="system",
        is_system_config=True,
    )
    return db_template


def get_activity_template_by_id(
    db: Session, template_id: int, include_deleted: bool = False
) -> models.ActivityTemplate:
    query = db.query(models.ActivityTemplate).filter(models.ActivityTemplate.id == template_id)
    if not include_deleted:
        query = query.filter(models.ActivityTemplate.is_deleted == False)
    template = query.first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity Template not found"
        )
    return template


def get_activity_templates(
    db: Session, include_deleted: bool = False, skip: int = 0, limit: int = 100
) -> List[models.ActivityTemplate]:
    query = db.query(models.ActivityTemplate)
    if not include_deleted:
        query = query.filter(models.ActivityTemplate.is_deleted == False)
    return (
        query.order_by(models.ActivityTemplate.name)
             .offset(skip)
             .limit(limit)
             .all()
    )


def update_activity_template(
    db: Session,
    template_data: schemas.ActivityTemplateUpdate,
    current_user_info: dict,
) -> models.ActivityTemplate:
    db_template = get_activity_template_by_id(db, template_data.id)
    original_data = serialize_data(
        {c.name: getattr(db_template, c.name) for c in db_template.__table__.columns}
    )

    _validate_name_unique(db, template_data.name, exclude_id=template_data.id)
    _validate_care_centre_exists(db, template_data.care_centre_id)

    current_user_id = current_user_info.get("id") or template_data.modified_by_id
    update_data = template_data.model_dump(exclude={"id", "modified_by_id"})
    for field, value in update_data.items():
        setattr(db_template, field, value)
    db_template.modified_by_id = current_user_id

    try:
        db.commit()
        db.refresh(db_template)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Activity Template: {str(e)}")

    updated_data_dict = serialize_data(update_data)
    log_crud_action(
        action=ActionType.UPDATE,
        user=current_user_id,
        user_full_name=current_user_info.get("fullname"),
        message=with_change_summary(
            f"Updated Activity Template: {db_template.name}", original_data, updated_data_dict
        ),
        table="ACTIVITY_TEMPLATE",
        entity_id=db_template.id,
        original_data=original_data,
        updated_data=updated_data_dict,
        log_type="system",
        is_system_config=True,
    )
    return db_template


def delete_activity_template(
    db: Session, template_id: int, current_user_info: dict
) -> models.ActivityTemplate:
    """Soft-delete.

    Nothing cascades. Activities and centre activities created from a template
    hold no reference back to it, so deleting a template has no effect on
    anything it has already produced - which is the intended behaviour, not an
    oversight.
    """
    db_template = get_activity_template_by_id(db, template_id)
    original_data = serialize_data(
        {c.name: getattr(db_template, c.name) for c in db_template.__table__.columns}
    )

    current_user_id = current_user_info.get("id")
    db_template.is_deleted = True
    db_template.modified_by_id = current_user_id

    try:
        db.commit()
        db.refresh(db_template)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Activity Template: {str(e)}")

    log_crud_action(
        action=ActionType.DELETE,
        user=current_user_id,
        user_full_name=current_user_info.get("fullname"),
        message=f"Deleted Activity Template: {db_template.name}",
        table="ACTIVITY_TEMPLATE",
        entity_id=db_template.id,
        original_data=original_data,
        updated_data=serialize_data({"is_deleted": True}),
        log_type="system",
        is_system_config=True,
    )
    return db_template

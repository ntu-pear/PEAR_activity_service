from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.crud.activity_template_crud import (
    create_activity_template,
    delete_activity_template,
    get_activity_template_by_id,
    get_activity_templates,
    update_activity_template,
)
from app.models.activity_template_model import ActivityTemplate as ActivityTemplateModel
from app.schemas.activity_template_schema import (
    ActivityTemplateCreate,
    ActivityTemplateUpdate,
)


@pytest.fixture
def base_template_data():
    return {
        "name": "Breathing (standard)",
        "title": "Breathing",
        "description": "A breathing exercise",
        "is_compulsory": True,
        "is_fixed": True,
        "is_group": False,
        "start_date": date.today(),
        "end_date": date(2999, 1, 1),
        "min_duration": 60,
        "max_duration": 60,
        "min_people_req": 1,
        "fixed_time_slots": "Monday 09:00,Tuesday 09:00",
        "created_by_id": "1",
    }


@pytest.fixture
def create_template_schema(base_template_data):
    return ActivityTemplateCreate(**base_template_data)


#===== Schema =========
def test_template_uses_the_shared_activity_rules(base_template_data):
    """A template that could not produce a valid centre activity is rejected.

    Proves the extraction in activity_rules.py is actually wired up here rather
    than the template schema carrying its own copy.
    """
    with pytest.raises(ValidationError) as exc:
        ActivityTemplateCreate(**{**base_template_data, "is_group": True, "min_people_req": 1})
    assert "Group activities must have a minimum of 2" in str(exc.value)


def test_template_allows_a_start_date_in_the_past(base_template_data):
    """A template's start_date is a stored default, not a scheduled date.

    CentreActivityCreate rejects a past start_date; a template saved months ago
    must not become un-editable because of it. The check applies when the
    template is applied, not when it is saved.
    """
    schema = ActivityTemplateCreate(**{**base_template_data, "start_date": date(2020, 1, 1)})
    assert schema.start_date == date(2020, 1, 1)


def test_template_name_is_separate_from_activity_title(create_template_schema):
    """name labels the template; title becomes the Activity."""
    assert create_template_schema.name == "Breathing (standard)"
    assert create_template_schema.title == "Breathing"


def test_template_has_no_activity_id(base_template_data):
    """A template is a blank form - the activity does not exist until it is applied."""
    schema = ActivityTemplateCreate(**base_template_data)
    assert not hasattr(schema, "activity_id")


#===== CREATE =========
@patch("app.crud.activity_template_crud.log_crud_action", lambda *a, **k: None)
def test_create_template_success(get_db_session_mock, mock_supervisor_user, create_template_schema):
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    result = create_activity_template(
        db=get_db_session_mock,
        template_data=create_template_schema,
        current_user_info=mock_supervisor_user,
    )

    assert result.name == create_template_schema.name
    assert result.title == create_template_schema.title
    get_db_session_mock.add.assert_called_once()
    get_db_session_mock.commit.assert_called_once()


@patch("app.crud.activity_template_crud.log_crud_action", lambda *a, **k: None)
def test_create_template_duplicate_name_fails(
    get_db_session_mock, mock_supervisor_user, create_template_schema
):
    """Template names identify templates in the picker, so they must be distinct."""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = MagicMock()

    with pytest.raises(HTTPException) as exc:
        create_activity_template(
            db=get_db_session_mock,
            template_data=create_template_schema,
            current_user_info=mock_supervisor_user,
        )

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in exc.value.detail


@patch("app.crud.activity_template_crud._validate_name_unique", lambda *a, **k: None)
@patch("app.crud.activity_template_crud.log_crud_action", lambda *a, **k: None)
def test_create_template_missing_care_centre_fails(
    get_db_session_mock, mock_supervisor_user, base_template_data
):
    schema = ActivityTemplateCreate(**{**base_template_data, "care_centre_id": 99})
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        create_activity_template(
            db=get_db_session_mock,
            template_data=schema,
            current_user_info=mock_supervisor_user,
        )

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Care Centre not found"


@patch("app.crud.activity_template_crud._validate_name_unique", lambda *a, **k: None)
@patch("app.crud.activity_template_crud.log_crud_action", lambda *a, **k: None)
def test_create_template_publishes_no_event(
    get_db_session_mock, mock_supervisor_user, create_template_schema
):
    """Saving a template writes one row and nothing else.

    No outbox row, so only the template itself is added. The Scheduler has no
    concept of a template and must never hear about one.
    """
    create_activity_template(
        db=get_db_session_mock,
        template_data=create_template_schema,
        current_user_info=mock_supervisor_user,
    )
    assert get_db_session_mock.add.call_count == 1


#===== READ =========
def test_get_template_by_id_not_found(get_db_session_mock):
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        get_activity_template_by_id(db=get_db_session_mock, template_id=999)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_templates_excludes_deleted_by_default(get_db_session_mock):
    chain = (
        get_db_session_mock.query.return_value
        .filter.return_value
        .order_by.return_value
        .offset.return_value
        .limit.return_value
    )
    chain.all.return_value = [MagicMock(), MagicMock()]

    result = get_activity_templates(db=get_db_session_mock, skip=0, limit=10)

    assert len(result) == 2
    get_db_session_mock.query.return_value.filter.assert_called_once()


#===== DELETE =========
@patch("app.crud.activity_template_crud.get_activity_template_by_id")
@patch("app.crud.activity_template_crud.log_crud_action", lambda *a, **k: None)
def test_delete_template_does_not_cascade(
    mock_get, get_db_session_mock, mock_supervisor_user
):
    """Deleting a template must not touch anything created from it.

    Activities and centre activities hold no reference back to the template they
    came from - that absence is deliberate, so a template is a convenience for
    creating rows rather than a permanent property of them.
    """
    # A real model instance rather than a mock: the CRUD reads __table__.columns
    # to snapshot the row for the audit log, which a MagicMock cannot provide.
    template = ActivityTemplateModel(
        id=1, name="Breathing (standard)", title="Breathing", is_deleted=False
    )
    mock_get.return_value = template

    result = delete_activity_template(
        db=get_db_session_mock, template_id=1, current_user_info=mock_supervisor_user
    )

    assert result.is_deleted is True
    get_db_session_mock.commit.assert_called_once()

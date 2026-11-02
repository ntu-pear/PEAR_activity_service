from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.crud.apply_template_crud import apply_activity_template
from app.schemas.apply_template_schema import ApplyTemplateRequest


@pytest.fixture
def apply_payload_data():
    return {
        "name": "Breathing AM",
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
    }


@pytest.fixture
def apply_payload(apply_payload_data):
    return ApplyTemplateRequest(**apply_payload_data)


#===== Schema =========
def test_apply_uses_the_shared_activity_rules(apply_payload_data):
    with pytest.raises(ValidationError) as exc:
        ApplyTemplateRequest(**{**apply_payload_data, "is_group": True, "min_people_req": 1})
    assert "Group activities must have a minimum of 2" in str(exc.value)


def test_apply_rejects_a_start_date_in_the_past(apply_payload_data):
    """Unlike the stored template, what apply produces is scheduled.

    A template saved months ago carries a stale start_date; the supervisor is
    expected to adjust it before submitting, and this is what makes them.
    """
    with pytest.raises(ValidationError) as exc:
        ApplyTemplateRequest(**{**apply_payload_data, "start_date": date.today() - timedelta(days=1)})
    assert "Start date cannot be in the past" in str(exc.value)


#===== Apply =========
@patch("app.crud.apply_template_crud.create_centre_activity")
@patch("app.crud.apply_template_crud.create_activity")
@patch("app.crud.apply_template_crud.get_activity_template_by_id")
def test_apply_creates_activity_when_none_exists(
    mock_template, mock_create_activity, mock_create_ca,
    get_db_session_mock, mock_supervisor_user, apply_payload
):
    mock_template.return_value = MagicMock(id=1)
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    mock_create_activity.return_value = MagicMock(id=12, title="Breathing")
    mock_create_ca.return_value = MagicMock(id=40, name="Breathing AM")

    activity, centre_activity, was_created = apply_activity_template(
        db=get_db_session_mock, template_id=1, payload=apply_payload,
        current_user_info=mock_supervisor_user,
    )

    assert was_created is True
    mock_create_activity.assert_called_once()
    assert activity.id == 12
    assert centre_activity.id == 40
    get_db_session_mock.commit.assert_called_once()


@patch("app.crud.apply_template_crud.create_centre_activity")
@patch("app.crud.apply_template_crud.create_activity")
@patch("app.crud.apply_template_crud.get_activity_template_by_id")
def test_apply_reuses_an_existing_activity(
    mock_template, mock_create_activity, mock_create_ca,
    get_db_session_mock, mock_supervisor_user, apply_payload
):
    """Applying the same template a second time must not create a second activity.

    This is what lets Breathing AM and Breathing PM live under one Breathing
    activity. Creating another would hit the duplicate-title guard anyway.
    """
    mock_template.return_value = MagicMock(id=1)
    existing = MagicMock(id=12, title="Breathing")
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing
    mock_create_ca.return_value = MagicMock(id=41, name="Breathing PM")

    activity, centre_activity, was_created = apply_activity_template(
        db=get_db_session_mock, template_id=1, payload=apply_payload,
        current_user_info=mock_supervisor_user,
    )

    assert was_created is False
    assert activity is existing
    mock_create_activity.assert_not_called()
    assert centre_activity.id == 41


@patch("app.crud.apply_template_crud.create_centre_activity")
@patch("app.crud.apply_template_crud.create_activity")
@patch("app.crud.apply_template_crud.get_activity_template_by_id")
def test_apply_reuse_does_not_modify_the_activity(
    mock_template, mock_create_activity, mock_create_ca,
    get_db_session_mock, mock_supervisor_user, apply_payload
):
    """Reuse means reuse: no update, so no activity event.

    If this started writing to the activity, editing the description while adding
    Breathing PM would silently change what Breathing AM displays.
    """
    mock_template.return_value = MagicMock(id=1)
    existing = MagicMock(id=12, title="Breathing", description="original")
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing
    mock_create_ca.return_value = MagicMock(id=41)

    apply_activity_template(
        db=get_db_session_mock, template_id=1, payload=apply_payload,
        current_user_info=mock_supervisor_user,
    )

    assert existing.description == "original"
    get_db_session_mock.add.assert_not_called()


@patch("app.crud.apply_template_crud.create_centre_activity")
@patch("app.crud.apply_template_crud.create_activity")
@patch("app.crud.apply_template_crud.get_activity_template_by_id")
def test_apply_uses_distinct_correlation_ids(
    mock_template, mock_create_activity, mock_create_ca,
    get_db_session_mock, mock_supervisor_user, apply_payload
):
    """The two events must not share a correlation id.

    The scheduler's consumer discards a correlation id it has already processed,
    so sharing one means the centre activity event is silently dropped. That is
    the defect that cost ten months of drift on the cascade path; apply is the
    next place in the system with the same shape.
    """
    mock_template.return_value = MagicMock(id=1)
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    mock_create_activity.return_value = MagicMock(id=12, title="Breathing")
    mock_create_ca.return_value = MagicMock(id=40)

    apply_activity_template(
        db=get_db_session_mock, template_id=1, payload=apply_payload,
        current_user_info=mock_supervisor_user,
    )

    activity_cid = mock_create_activity.call_args.kwargs["correlation_id"]
    centre_activity_cid = mock_create_ca.call_args.kwargs["correlation_id"]

    assert activity_cid
    assert centre_activity_cid
    assert activity_cid != centre_activity_cid


@patch("app.crud.apply_template_crud.create_centre_activity")
@patch("app.crud.apply_template_crud.create_activity")
@patch("app.crud.apply_template_crud.get_activity_template_by_id")
def test_apply_defers_both_commits_to_itself(
    mock_template, mock_create_activity, mock_create_ca,
    get_db_session_mock, mock_supervisor_user, apply_payload
):
    """Both creates run with commit=False so one transaction covers them.

    Letting either commit on its own would mean a failure in the second leaves
    the first behind - an activity nobody can schedule, with nothing to retry it.
    """
    mock_template.return_value = MagicMock(id=1)
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    mock_create_activity.return_value = MagicMock(id=12, title="Breathing")
    mock_create_ca.return_value = MagicMock(id=40)

    apply_activity_template(
        db=get_db_session_mock, template_id=1, payload=apply_payload,
        current_user_info=mock_supervisor_user,
    )

    assert mock_create_activity.call_args.kwargs["commit"] is False
    assert mock_create_ca.call_args.kwargs["commit"] is False
    get_db_session_mock.commit.assert_called_once()


@patch("app.crud.apply_template_crud.create_centre_activity")
@patch("app.crud.apply_template_crud.create_activity")
@patch("app.crud.apply_template_crud.get_activity_template_by_id")
def test_apply_rolls_back_when_the_centre_activity_fails(
    mock_template, mock_create_activity, mock_create_ca,
    get_db_session_mock, mock_supervisor_user, apply_payload
):
    """A failure in the second write must leave no activity behind."""
    mock_template.return_value = MagicMock(id=1)
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    mock_create_activity.return_value = MagicMock(id=12, title="Breathing")
    mock_create_ca.side_effect = HTTPException(status_code=400, detail="duplicate")

    with pytest.raises(HTTPException) as exc:
        apply_activity_template(
            db=get_db_session_mock, template_id=1, payload=apply_payload,
            current_user_info=mock_supervisor_user,
        )

    assert exc.value.status_code == 400
    get_db_session_mock.rollback.assert_called_once()
    get_db_session_mock.commit.assert_not_called()


@patch("app.crud.apply_template_crud.get_activity_template_by_id")
def test_apply_against_a_missing_template_is_rejected(
    mock_template, get_db_session_mock, mock_supervisor_user, apply_payload
):
    """Soft-deleted templates cannot be applied."""
    mock_template.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Activity Template not found"
    )

    with pytest.raises(HTTPException) as exc:
        apply_activity_template(
            db=get_db_session_mock, template_id=999, payload=apply_payload,
            current_user_info=mock_supervisor_user,
        )

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

from datetime import datetime, timedelta
from unittest import mock

import pytest

# from conftest import existing_activity, get_db_session_mock
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.models.activity_model as models
from app.crud.activity_crud import (
    create_activity,
    delete_activity_by_id,
    get_activities,
    get_activity_by_id,
    update_activity_by_id,
)
from app.models.activity_model import Activity
from app.schemas.activity_schema import ActivityCreate


# Stub out real logging so we don’t try to JSON‑serialize MagicMocks
@pytest.fixture(autouse=True)
def disable_crud_logging(monkeypatch):
    from app.crud import activity_crud
    monkeypatch.setattr(activity_crud, "log_crud_action", lambda *args, **kwargs: None)

@pytest.fixture
def activity_data():
    """Sample input for create/update."""
    return ActivityCreate(
        title="Morning Jog",
        description="A quick run in the park",
        start_date=datetime(2025, 1, 1, 7, 0, 0),
        end_date=datetime(2025, 1, 1, 8, 0, 0)
    )

@mock.patch("app.crud.activity_crud.get_outbox_service")
@mock.patch("app.models.activity_model.Activity")
def test_create_activity(mock_activity_cls, get_db_session_mock, activity_data):
    """Should create, commit, refresh, and return the new Activity."""
    # duplicate check to return no existing activity
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    fake_obj = mock_activity_cls.return_value
    result = create_activity(get_db_session_mock, activity_in=activity_data, current_user_info={"id": "test-user", "fullname": "Test User"})
    assert result is fake_obj

@mock.patch("app.models.activity_model.Activity")
def test_create_activity_duplicate(mock_activity_cls, get_db_session_mock, activity_data):
    """Should 400 if an Activity with the same title already exists."""
    fake_existing = mock.MagicMock(spec=Activity)
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = fake_existing

    with pytest.raises(HTTPException) as exc:
        create_activity(get_db_session_mock, activity_in=activity_data, current_user_info={"id": "test-user", "fullname": "Test User"})
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == "Activity already exists"

@mock.patch("app.crud.activity_crud.get_outbox_service")
@mock.patch("app.crud.activity_crud.get_activity_by_id")
def test_update_activity_by_id_success(mock_get, get_db_session_mock, existing_activity, activity_data):
    """Should update fields, commit, refresh, and return the Activity."""
    mock_get.return_value = existing_activity
    result = update_activity_by_id(
        get_db_session_mock, activity_id=existing_activity.id, activity_in=activity_data, current_user_info={"id": "test-user", "fullname": "Test User"}
    )
    assert result is existing_activity

@mock.patch("app.crud.activity_crud.get_activity_by_id")
def test_update_activity_by_id_not_found(mock_get, get_db_session_mock, activity_data):
    """Should 404 if the Activity does not exist."""
    mock_get.return_value = None
    with pytest.raises(HTTPException) as exc:
        update_activity_by_id(get_db_session_mock, activity_id=999, activity_in=activity_data, current_user_info={"id": "test-user", "fullname": "Test User"})
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

@mock.patch("app.crud.activity_crud.get_outbox_service")
@mock.patch("app.crud.activity_crud.get_activity_by_id")
def test_delete_activity_by_id_success(mock_get, get_db_session_mock, existing_activity):
    """Should mark is_deleted, commit, refresh, and return."""
    mock_get.return_value = existing_activity
    result = delete_activity_by_id(get_db_session_mock, activity_id=existing_activity.id, current_user_info={"id": "test-user", "fullname": "Test User"})
    assert result.is_deleted

@mock.patch("app.crud.activity_crud.get_activity_by_id")
def test_delete_activity_by_id_not_found(mock_get, get_db_session_mock):
    """Should 404 if trying to delete a missing Activity."""
    mock_get.return_value = None
    with pytest.raises(HTTPException) as exc:
        delete_activity_by_id(get_db_session_mock, activity_id=999, current_user_info={"id": "test-user", "fullname": "Test User"})
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_activity_by_id_found(get_db_session_mock, existing_activity):
    """Should return an Activity if it exists and is not deleted."""
    query_mock = get_db_session_mock.query.return_value
    filter1_mock = query_mock.filter.return_value
    filter2_mock = filter1_mock.filter.return_value
    filter2_mock.first.return_value = existing_activity

    result = get_activity_by_id(get_db_session_mock, activity_id=1)

    get_db_session_mock.query.assert_called_once_with(models.Activity)
    assert result == existing_activity

def test_get_activity_by_id_not_found(get_db_session_mock):
    """Should return None if no matching Activity."""
    query_mock = get_db_session_mock.query.return_value
    filter1_mock = query_mock.filter.return_value
    filter2_mock = filter1_mock.filter.return_value
    filter2_mock.first.return_value = None

    result = get_activity_by_id(get_db_session_mock, activity_id=999)
    assert result is None

def test_get_activities(get_db_session_mock):
    """Should return a list of activities, honoring skip & limit."""
    activities_list = [mock.MagicMock(), mock.MagicMock()]
    chain = (
        get_db_session_mock.query.return_value
        .filter.return_value
        .order_by.return_value
        .offset.return_value
        .limit.return_value
    )
    chain.all.return_value = activities_list

    result = get_activities(get_db_session_mock, skip=5, limit=2)
    assert result == activities_list



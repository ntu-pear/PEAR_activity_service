import pytest
from unittest import mock
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud.activity_crud import (
    get_activity_by_id,
    get_activities,
    create_activity,
    update_activity_by_id,
    delete_activity_by_id,
)
from app.models.activity_model import Activity
from app.schemas.activity_schema import ActivityCreate
import app.models.activity_model as models

from tests.utils.mock_db import get_db_session_mock

@pytest.fixture
def db_session_mock():
    """Fixture to mock the DB session."""
    return get_db_session_mock()

@pytest.fixture
def activity_data():
    """Sample input for create/update."""
    return ActivityCreate(
        title="Morning Jog",
        description="A quick run in the park",
        start_date=datetime(2025, 1, 1, 7, 0, 0),
        end_date=datetime(2025, 1, 1, 8, 0, 0),
        active=True,
    )

@pytest.fixture
def existing_activity():
    """A fake Activity instance for retrieval/update/delete."""
    activity = mock.MagicMock(spec=Activity)
    activity.id = 1
    activity.active = True
    activity.is_deleted = False
    activity.title = "Old Title"
    activity.description = "Old Description"
    activity.start_date = datetime(2025, 1, 1, 6, 0, 0)
    activity.end_date = datetime(2025, 1, 1, 7, 0, 0)
    return activity

@mock.patch("app.models.activity_model.Activity")
def test_create_activity(mock_activity_cls, db_session_mock, activity_data):
    """Should instantiate, add, commit, refresh, and return the new Activity."""
    fake_obj = mock_activity_cls.return_value

    result = create_activity(db_session_mock, activity_in=activity_data)

    # ensure we called the model constructor correctly
    mock_activity_cls.assert_called_once_with(**activity_data.model_dump(by_alias=True))
    db_session_mock.add.assert_called_once_with(fake_obj)
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(fake_obj)
    assert result is fake_obj


def test_get_activity_by_id_found(db_session_mock, existing_activity):
    """Should return an Activity if it exists and is not deleted."""
    query_mock = db_session_mock.query.return_value
    filter_mock = query_mock.filter.return_value
    filter_mock.first.return_value = existing_activity

    result = get_activity_by_id(db_session_mock, activity_id=1)

    db_session_mock.query.assert_called_once_with(models.Activity)
    query_mock.filter.assert_called_once()
    filter_mock.first.assert_called_once()
    assert result == existing_activity


def test_get_activity_by_id_not_found(db_session_mock):
    """Should return None if no matching Activity."""
    db_session_mock.query.return_value.filter.return_value.first.return_value = None

    result = get_activity_by_id(db_session_mock, activity_id=999)
    assert result is None


def test_get_activities(db_session_mock):
    """Should return a list of activities, honoring skip & limit."""
    activities_list = [mock.MagicMock(), mock.MagicMock()]
    chain = (
        db_session_mock.query.return_value
        .filter.return_value
        .order_by.return_value
        .offset.return_value
        .limit.return_value
    )
    chain.all.return_value = activities_list

    result = get_activities(db_session_mock, skip=5, limit=2)
    assert result == activities_list


def test_update_activity_by_id_success(db_session_mock, existing_activity, activity_data):
    """Should update fields, commit, refresh, and return the Activity."""
    with mock.patch("app.crud.activity_crud.get_activity_by_id", return_value=existing_activity):
        result = update_activity_by_id(
            db_session_mock,
            activity_id=existing_activity.id,
            activity_in=activity_data,
        )

        update_data = activity_data.model_dump(by_alias=True, exclude_unset=True)
        for field, value in update_data.items():
            assert getattr(existing_activity, field) == value

        db_session_mock.commit.assert_called_once()
        db_session_mock.refresh.assert_called_once_with(existing_activity)
        assert result == existing_activity


def test_update_activity_by_id_not_found(db_session_mock, activity_data):
    """Should 404 if the Activity does not exist."""
    with mock.patch("app.crud.activity_crud.get_activity_by_id", return_value=None):
        with pytest.raises(HTTPException) as exc:
            update_activity_by_id(db_session_mock, activity_id=999, activity_in=activity_data)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Activity not found" in exc.value.detail


def test_delete_activity_by_id_success(db_session_mock, existing_activity):
    """Should mark is_deleted, add, commit, refresh, and return."""
    with mock.patch("app.crud.activity_crud.get_activity_by_id", return_value=existing_activity):
        result = delete_activity_by_id(db_session_mock, activity_id=existing_activity.id)

        assert existing_activity.is_deleted is True
        db_session_mock.add.assert_called_once_with(existing_activity)
        db_session_mock.commit.assert_called_once()
        db_session_mock.refresh.assert_called_once_with(existing_activity)
        assert result == existing_activity


def test_delete_activity_by_id_not_found(db_session_mock):
    """Should 404 if trying to delete a missing Activity."""
    with mock.patch("app.crud.activity_crud.get_activity_by_id", return_value=None):
        with pytest.raises(HTTPException) as exc:
            delete_activity_by_id(db_session_mock, activity_id=999)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc.value.detail == "Activity not found or already deleted"
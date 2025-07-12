import pytest
from unittest.mock import MagicMock, create_autospec
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.activity_model import Activity
from app.models.centre_activity_model import CentreActivity


@pytest.fixture()
def get_db_session_mock():
    """Fixture to create a mock database session."""
    return create_autospec(Session, instance=True)

@pytest.fixture
def mock_current_user():
    return {
        "id": "2",
        "fullName": "Test User",
        "email": "test@test.com",
        "roleName": "SUPERVISOR",
    }

#====== Activity ======

@pytest.fixture
def base_activity_data():
    """Base data for Activity"""
    return {
        "id": 1,
        "active": True,
        "is_deleted": False,
        "title": "Old Title",
        "description": "Old Description",
        "start_date": datetime(2025, 1, 1, 6, 0),
        "end_date": datetime(2025, 1, 1, 7, 0),
    }

@pytest.fixture
def existing_activity(base_activity_data):
    """An Activity instance for retrieval/update/delete."""
    return Activity(**base_activity_data)


# --- Centre Activity Fixtures ---
@pytest.fixture
def base_centre_activity_data_list():
    """Base data for Centre Activity"""
    return [
        {
            "id": 1,
            "activity_id": 1,
            "is_deleted": False,
            "is_compulsory": True,
            "is_fixed": False,
            "is_group": False,
            "start_date": datetime.now().date(),
            "end_date": None,
            "min_duration": 30,
            "max_duration": 60,
            "min_people_req": 1,
            "created_by_id": "1",
            "modified_by_id": "1",
            "created_date": datetime.now(),
            "modified_date": datetime.now(),
        },
        {
            "id": 1,
            "activity_id": 2,
            "is_deleted": False,
            "is_compulsory": True,
            "is_fixed": True,
            "is_group": True,
            "start_date": datetime.now().date(),
            "end_date": None,
            "min_duration": 60,
            "max_duration": 60,
            "min_people_req": 4,
            "created_by_id": "2",
            "modified_by_id": "2",
            "created_date": datetime.now(),
            "modified_date": datetime.now(),
        },
    ]

@pytest.fixture
def base_centre_activity_data(base_centre_activity_data_list):
    return base_centre_activity_data_list[0]

@pytest.fixture
def existing_centre_activity(base_centre_activity_data):
    """A CentreActivity instance for mocking DB data"""
    return CentreActivity(**base_centre_activity_data)

@pytest.fixture
def existing_centre_activities(base_centre_activity_data_list):
    """A list of CentreActivity instance for mocking DB data"""
    return [CentreActivity(**data) for data in base_centre_activity_data_list]

@pytest.fixture
def soft_deleted_centre_activity(base_centre_activity_data):
    """Soft-deleted CentreActivity instance"""
    data = base_centre_activity_data.copy()
    data.update({
        "id": 2,  # Different ID
        "is_deleted": True,
        "modified_date": datetime.now()
    })
    return CentreActivity(**data)

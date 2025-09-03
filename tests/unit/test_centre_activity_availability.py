import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from app.models.centre_activity_availability_model import CentreActivityAvailability
from app.schemas.centre_activity_availability_schema import CentreActivityAvailabilityCreate
from app.crud.centre_activity_availability_crud import( 
    create_centre_activity_availability,
    get_centre_activity_availabilities,
    get_centre_activity_availability_by_id,
    update_centre_activity_availability,
    delete_centre_activity_availability
)
from app.routers.centre_activity_availability_router import (
    create_centre_activity_availability as router_create_centre_activity_availability,
    get_all_centre_activity_availabilities as router_get_all_centre_activity_availabilities,
    get_centre_activity_availability_by_id as router_get_centre_activity_availability_by_id,
    update_centre_activity_availability as router_update_centre_activity_availability,
    delete_centre_activity_availability as router_delete_centre_activity_availability
)

# ===== GET tests ======
def test_get_centre_activity_availability_by_id_success(get_db_session_mock, existing_centre_activity_availability):
    
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = existing_centre_activity_availability

    result = get_centre_activity_availability_by_id(get_db_session_mock, centre_activity_availability_id=1)
    assert result == existing_centre_activity_availability
    assert result.id == 1

def test_get_centre_activity_availability_by_id_not_found(get_db_session_mock):
    
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        get_centre_activity_availability_by_id(get_db_session_mock, centre_activity_availability_id=999)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_centre_activity_availability_by_id_include_deleted(get_db_session_mock, soft_deleted_centre_activity_availability):
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = soft_deleted_centre_activity_availability

    result = get_centre_activity_availability_by_id(get_db_session_mock, centre_activity_availability_id=1, include_deleted=True)
    assert result == soft_deleted_centre_activity_availability
    assert result.is_deleted == True

def test_get_centre_activity_availabilities_success(get_db_session_mock, existing_centre_activity_availabilities):
    get_db_session_mock.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = existing_centre_activity_availabilities

    result = get_centre_activity_availabilities(get_db_session_mock, include_deleted=False)
    assert len(result) == 2

    for actual_data, expected_data in zip(result, existing_centre_activity_availabilities):
        assert actual_data.id == expected_data.id
        assert actual_data.centre_activity_id == expected_data.centre_activity_id
        assert actual_data.is_deleted == expected_data.is_deleted
        assert actual_data.start_time == expected_data.start_time
        assert actual_data.end_time == expected_data.end_time
        assert actual_data.created_by_id == expected_data.created_by_id
        assert actual_data.modified_by_id == expected_data.modified_by_id

def test_get_centre_activity_availabilities_include_deleted(get_db_session_mock, soft_deleted_centre_activity_availabilities):
    
    get_db_session_mock.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = soft_deleted_centre_activity_availabilities

    result = get_centre_activity_availabilities(get_db_session_mock, include_deleted=True)
    for actual_data, expected_data in zip(result, soft_deleted_centre_activity_availabilities):
        assert actual_data.id == expected_data.id
        assert actual_data.is_deleted == expected_data.is_deleted
        assert actual_data.created_by_id == expected_data.created_by_id
        assert actual_data.modified_by_id == expected_data.modified_by_id

def test_get_centre_activity_availabilities_include_deleted(get_db_session_mock, soft_deleted_centre_activity_availabilities):

    get_db_session_mock.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = soft_deleted_centre_activity_availabilities

    result = get_centre_activity_availabilities(get_db_session_mock, include_deleted=True)
    assert len(result) == 2

    for actual_data, expected_data in zip(result, soft_deleted_centre_activity_availabilities):
        assert actual_data.id == expected_data.id
        assert actual_data.centre_activity_id == expected_data.centre_activity_id
        assert actual_data.is_deleted == expected_data.is_deleted
        assert actual_data.start_time == expected_data.start_time
        assert actual_data.end_time == expected_data.end_time
        assert actual_data.created_by_id == expected_data.created_by_id
        assert actual_data.modified_by_id == expected_data.modified_by_id

# ===== CREATE tests ======
@patch("app.crud.centre_activity_availability_crud.get_care_centre_by_id")
@patch("app.crud.centre_activity_availability_crud.get_centre_activity_by_id")
def test_create_centre_activity_availability_not_recurring_success(
    mock_get_centre_activity,
    mock_get_care_centre_by_id,
    get_db_session_mock,
    mock_supervisor_user,
    create_centre_activity_availability_schema,
    existing_centre_activity,
):
    #Mock no duplicate record found
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None

    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity

    #Mock care centre response
    mock_get_care_centre = MagicMock()
    mock_get_care_centre = SimpleNamespace(
        id=1,
        is_deleted=False,
        name="Test Care Centre",
        country_code="SGP",
        address="123 Test St",
        postal_code="123456",
        contact_no="6512345678",
        email="test@gmail.com",
        no_of_devices_avail=10,
        working_hours = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday": {"open": "09:00", "close": "17:00"},
            "friday": {"open": "09:00", "close": "17:00"},
            "saturday": {"open": None, "close": None},
            "sunday": {"open": None, "close": None}
        },
        remarks="Test remarks",
        created_by_id="1",
        created_date=datetime.now(),
        modified_by_id=None,
        modified_date=None,
    )

    mock_get_care_centre_by_id.return_value = mock_get_care_centre
    
    result = create_centre_activity_availability(
        db=get_db_session_mock,
        centre_activity_availability_data=create_centre_activity_availability_schema,
        current_user_info=mock_supervisor_user
    )
    
    assert result[0].centre_activity_id == create_centre_activity_availability_schema.centre_activity_id
    assert result[0].created_by_id == create_centre_activity_availability_schema.created_by_id
    assert result[0].start_time.replace(tzinfo=timezone.utc, second=0, microsecond=0) == create_centre_activity_availability_schema.start_time
    assert result[0].end_time.replace(tzinfo=timezone.utc, second=0, microsecond=0) == create_centre_activity_availability_schema.end_time

@patch("app.crud.centre_activity_availability_crud.get_care_centre_by_id")
@patch("app.crud.centre_activity_availability_crud.get_centre_activity_by_id")
def test_create_centre_activity_availability_recurring_success(
    mock_get_centre_activity,
    mock_get_care_centre_by_id,
    get_db_session_mock,
    mock_supervisor_user,
    create_centre_activity_availability_schema,
    existing_centre_activity,
    create_centre_activity_availability_schema_recurring
):
    #Mock no duplicate record found
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None

    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity

    #Mock care centre response
    mock_get_care_centre = MagicMock()
    mock_get_care_centre = SimpleNamespace(
        id=1,
        is_deleted=False,
        name="Test Care Centre",
        country_code="SGP",
        address="123 Test St",
        postal_code="123456",
        contact_no="6512345678",
        email="test@gmail.com",
        no_of_devices_avail=10,
        working_hours = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday": {"open": "09:00", "close": "17:00"},
            "friday": {"open": "09:00", "close": "17:00"},
            "saturday": {"open": None, "close": None},
            "sunday": {"open": None, "close": None}
        },
        remarks="Test remarks",
        created_by_id="1",
        created_date=datetime.now(),
        modified_by_id=None,
        modified_date=None,
    )

    mock_get_care_centre_by_id.return_value = mock_get_care_centre
    
    result = create_centre_activity_availability(
        db=get_db_session_mock,
        centre_activity_availability_data=create_centre_activity_availability_schema,
        current_user_info=mock_supervisor_user,
        is_recurring_everyday=True
    )

    for actual_data, expected_data in zip(result, create_centre_activity_availability_schema_recurring):
        assert actual_data.centre_activity_id == expected_data.centre_activity_id
        assert actual_data.created_by_id == expected_data.created_by_id
        assert actual_data.start_time.replace(tzinfo=timezone.utc, second=0, microsecond=0) == expected_data.start_time
        assert actual_data.end_time.replace(tzinfo=timezone.utc, second=0, microsecond=0) == expected_data.end_time

def test_create_centre_activity_availability_duplicate_found(
    get_db_session_mock,
    mock_supervisor_user,
    existing_centre_activity_availability,
    create_centre_activity_availability_schema
):
    #Mock duplicate record found
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = existing_centre_activity_availability
    
    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=create_centre_activity_availability_schema,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Centre Activity Availability with these attributes exists or already soft deleted." in exc_info.value.detail["message"]
    assert existing_centre_activity_availability.id == int(exc_info.value.detail["existing_id"])
    assert existing_centre_activity_availability.is_deleted == exc_info.value.detail["existing_is_deleted"]

@patch("app.crud.centre_activity_availability_crud.get_care_centre_by_id")
@patch("app.crud.centre_activity_availability_crud.get_centre_activity_by_id")
def test_create_centre_activity_availability_invalid_date(
    mock_get_centre_activity,
    mock_get_care_centre_by_id,
    get_db_session_mock,
    existing_centre_activity,
    create_centre_activity_availability_schema_invalid,
    mock_supervisor_user
):
    #Mock no duplicate record found
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None

    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity
    
    #Mock care centre response
    mock_get_care_centre = MagicMock()
    mock_get_care_centre = SimpleNamespace(
        id=1,
        is_deleted=False,
        name="Test Care Centre",
        country_code="SGP",
        address="123 Test St",
        postal_code="123456",
        contact_no="6512345678",
        email="test@gmail.com",
        no_of_devices_avail=10,
        working_hours = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday": {"open": "09:00", "close": "17:00"},
            "friday": {"open": "09:00", "close": "17:00"},
            "saturday": {"open": None, "close": None},
            "sunday": {"open": None, "close": None}
        },
        remarks="Test remarks",
        created_by_id="1",
        created_date=datetime.now(),
        modified_by_id=None,
        modified_date=None,
    )

    mock_get_care_centre_by_id.return_value = mock_get_care_centre
    
    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=create_centre_activity_availability_schema_invalid,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Centre Activity Availability date cannot be on saturdays and sundays as the Care Centre is closed." in exc_info.value.detail["message"]

# ===== UPDATE tests ======
@patch("app.crud.centre_activity_availability_crud.get_care_centre_by_id")
@patch("app.crud.centre_activity_availability_crud.get_centre_activity_by_id")
def test_update_centre_activity_availability_success(
    mock_get_centre_activity,
    mock_get_care_centre_by_id,
    get_db_session_mock,
    mock_supervisor_user,
    update_centre_activity_availability_schema,
    existing_centre_activity_availability,
    existing_centre_activity
):
    #Mock centre activity availability record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_availability

    #Mock no duplicate of updated centre activity availability
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None
    
    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity
    
    #Mock care centre response
    mock_get_care_centre = MagicMock()
    mock_get_care_centre = SimpleNamespace(
        id=1,
        is_deleted=False,
        name="Test Care Centre",
        country_code="SGP",
        address="123 Test St",
        postal_code="123456",
        contact_no="6512345678",
        email="test@gmail.com",
        no_of_devices_avail=10,
        working_hours = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday": {"open": "09:00", "close": "17:00"},
            "friday": {"open": "09:00", "close": "17:00"},
            "saturday": {"open": None, "close": None},
            "sunday": {"open": None, "close": None}
        },
        remarks="Test remarks",
        created_by_id="1",
        created_date=datetime.now(),
        modified_by_id=None,
        modified_date=None,
    )

    mock_get_care_centre_by_id.return_value = mock_get_care_centre

    result = update_centre_activity_availability(
        db=get_db_session_mock,
        centre_activity_availability_data=update_centre_activity_availability_schema,
        current_user_info=mock_supervisor_user
    )
    assert result.centre_activity_id == update_centre_activity_availability_schema.centre_activity_id
    assert result.start_time.replace(tzinfo=timezone.utc, second=0, microsecond=0) == update_centre_activity_availability_schema.start_time
    assert result.end_time.replace(tzinfo=timezone.utc, second=0, microsecond=0) == update_centre_activity_availability_schema.end_time
    assert result.modified_by_id == update_centre_activity_availability_schema.modified_by_id
    assert result.modified_date.replace(tzinfo=timezone.utc, second=0, microsecond=0) == update_centre_activity_availability_schema.modified_date

def test_update_centre_activity_availability_fail(
        get_db_session_mock,
        update_centre_activity_availability_schema,
        mock_supervisor_user
    ):
     #Mock centre activity availability record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=update_centre_activity_availability_schema,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

def test_update_centre_activity_availability_duplicate_found(
        get_db_session_mock,
        mock_supervisor_user,
        update_centre_activity_availability_schema,
        update_centre_activity_availability_duplicate,
        existing_centre_activity_availability
    ):

    #Mock centre activity availability record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_availability

    #Mock duplicate of updated centre activity availability
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = update_centre_activity_availability_duplicate

    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=update_centre_activity_availability_schema,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Centre Activity Availability with these attributes exists or already soft deleted." in exc_info.value.detail["message"]
    assert existing_centre_activity_availability.id == int(exc_info.value.detail["existing_id"])
    assert existing_centre_activity_availability.is_deleted == exc_info.value.detail["existing_is_deleted"]

@patch("app.crud.centre_activity_availability_crud.get_care_centre_by_id")
@patch("app.crud.centre_activity_availability_crud.get_centre_activity_by_id")
def test_update_centre_activity_availability_invalid(
        mock_get_centre_activity,
        mock_get_care_centre_by_id,
        get_db_session_mock,
        mock_supervisor_user,
        update_centre_activity_availability_schema_invalid,
        existing_centre_activity_availability,
        existing_centre_activity
    ):

    #Mock centre activity availability record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_availability

    #Mock no duplicate of updated centre activity availability
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None
    
    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity
    
    #Mock care centre response
    mock_get_care_centre = MagicMock()
    mock_get_care_centre = SimpleNamespace(
        id=1,
        is_deleted=False,
        name="Test Care Centre",
        country_code="SGP",
        address="123 Test St",
        postal_code="123456",
        contact_no="6512345678",
        email="test@gmail.com",
        no_of_devices_avail=10,
        working_hours = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday": {"open": "09:00", "close": "17:00"},
            "friday": {"open": "09:00", "close": "17:00"},
            "saturday": {"open": None, "close": None},
            "sunday": {"open": None, "close": None}
        },
        remarks="Test remarks",
        created_by_id="1",
        created_date=datetime.now(),
        modified_by_id=None,
        modified_date=None,
    )

    mock_get_care_centre_by_id.return_value = mock_get_care_centre

    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=update_centre_activity_availability_schema_invalid,
            current_user_info=mock_supervisor_user
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Centre Activity Availability date cannot be on saturdays and sundays as the Care Centre is closed." in exc_info.value.detail["message"]

# ===== DELETE tests ======
def test_delete_centre_activity_availability_success(
    get_db_session_mock,
    mock_supervisor_user,
    existing_centre_activity_availability
):
    #Mock centre_activity_availability record exists
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_availability

    result = delete_centre_activity_availability(
        db=get_db_session_mock,
        centre_activity_availability_id=1,
        current_user_info=mock_supervisor_user
    )
    assert result == existing_centre_activity_availability

def test_delete_centre_activity_availability_fail(
    get_db_session_mock,
    mock_supervisor_user
):
    #Mock centre_activity_availability record not found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        delete_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_id=999,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Centre Activity Availability not found or already soft deleted." in exc_info.value.detail


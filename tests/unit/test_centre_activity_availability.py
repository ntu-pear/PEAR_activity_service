import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status

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

def test_get_centre_activity_availability_by_id_success(get_db_session_mock, existing_centre_activity_availability):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.filter.return_value.first.return_value = existing_centre_activity_availability

    result = get_centre_activity_availability_by_id(db, centre_activity_availability_id=1)
    assert result == existing_centre_activity_availability
    assert result.id == 1

def test_get_centre_activity_availability_by_id_not_found(get_db_session_mock):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_centre_activity_availability_by_id(db, centre_activity_availability_id=999)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_centre_activity_availability_by_id_include_deleted(get_db_session_mock, soft_deleted_centre_activity_availability):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.filter.return_value.first.return_value = soft_deleted_centre_activity_availability

    result = get_centre_activity_availability_by_id(db, centre_activity_availability_id=1, include_deleted=True)
    assert result == soft_deleted_centre_activity_availability
    assert result.id == 1
    assert result.is_deleted == True

def test_get_centre_activity_availabilities_success(get_db_session_mock, existing_centre_activity_availabilities):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.filter.return_value.first.return_value = existing_centre_activity_availabilities

    result = get_centre_activity_availabilities(db, include_deleted=False)
    assert len(result) == 2

    for actual_data, expected_data in zip(result, existing_centre_activity_availabilities):
        assert actual_data.id == expected_data.id
        assert actual_data.centre_activity_id == expected_data.centre_activity_id
        assert actual_data.is_deleted == expected_data.is_deleted
        assert actual_data.start_time == expected_data.start_time
        assert actual_data.end_time == expected_data.end_time
        assert actual_data.created_by_id == expected_data.created_by_id
        assert actual_data.modified_by_id == expected_data.modified_by_id

def test_get_centre_activity_availabilities_fail(get_db_session_mock):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_centre_activity_availabilities(db, include_deleted=False)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_centre_activity_availabilities_include_deleted(get_db_session_mock, soft_deleted_centre_activity_availabilities):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.filter.return_value.first.return_value = soft_deleted_centre_activity_availabilities

    result = get_centre_activity_availabilities(db, include_deleted=True)
    assert len(result) == 2

    for actual_data, expected_data in zip(result, soft_deleted_centre_activity_availabilities):
        assert actual_data.id == expected_data.id
        assert actual_data.centre_activity_id == expected_data.centre_activity_id
        assert actual_data.is_deleted == expected_data.is_deleted
        assert actual_data.start_time == expected_data.start_time
        assert actual_data.end_time == expected_data.end_time
        assert actual_data.created_by_id == expected_data.created_by_id
        assert actual_data.modified_by_id == expected_data.modified_by_id

@patch("app.crud.centre_activity_crud.get_centre_activity_by_id")
def test_updated_centre_activity_availability_success(
    get_db_session_mock, 
    mock_supervisor_user,
    mock_get_centre_activity_availability,
    existing_centre_activity_availability,
    update_centre_activity_availability_schema
):
    #Mock existing centre activity found
    mock_get_centre_activity_availability.return_value = existing_centre_activity_availability
    
    #Mock no duplicate centre activity availability
    mock_query = MagicMock()
    mock_query.filter.return_value.filter.return_value.first.return_value = None
    get_db_session_mock.query.return_value = mock_query

    result = update_centre_activity_availability(
        db=get_db_session_mock,
        centre_activity_availability_data=update_centre_activity_availability_schema,
        current_user_info=mock_supervisor_user
    )

    assert result.id == update_centre_activity_availability_schema.id
    assert result.centre_activity_id == update_centre_activity_availability_schema.centre_activity_id
    assert result.start_time == update_centre_activity_availability_schema.start_time
    assert result.end_time == update_centre_activity_availability_schema.end_time
    assert result.created_by_id == update_centre_activity_availability_schema.created_by_id
    assert result.modified_by_id == update_centre_activity_availability_schema.modified_by_id

    get_db_session_mock.add.assert_called_once()
    get_db_session_mock.commit.assert_called_once()

@patch("app.crud.centre_activity_crud.get_centre_activity_by_id")
def test_updated_centre_activity_availability_not_found(
    get_db_session_mock, 
    mock_supervisor_user,
    mock_get_centre_activity_availability,
    update_centre_activity_availability_schema
):
    #Mock existing centre activity not found
    mock_get_centre_activity_availability.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=update_centre_activity_availability_schema,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Centre Activity Availability not found or already soft deleted."


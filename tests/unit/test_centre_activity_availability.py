import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta, time
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
        assert actual_data.days_of_week == expected_data.days_of_week
        assert actual_data.start_time == expected_data.start_time
        assert actual_data.end_time == expected_data.end_time
        assert actual_data.start_date == expected_data.start_date
        assert actual_data.end_date == expected_data.end_date
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
        assert actual_data.days_of_week == expected_data.days_of_week
        assert actual_data.start_time == expected_data.start_time
        assert actual_data.end_time == expected_data.end_time
        assert actual_data.start_date == expected_data.start_date
        assert actual_data.end_date == expected_data.end_date
        assert actual_data.created_by_id == expected_data.created_by_id
        assert actual_data.modified_by_id == expected_data.modified_by_id

# ===== CREATE tests ======
@patch("app.crud.centre_activity_availability_crud.get_care_centre_by_id")
@patch("app.crud.centre_activity_availability_crud.get_centre_activity_by_id")
def test_create_centre_activity_availability_success(
    mock_get_centre_activity,
    mock_get_care_centre_by_id,
    get_db_session_mock,
    mock_supervisor_user,
    create_centre_activity_availability_schema,
    existing_centre_activity,
    existing_care_centre
):
    #Mock no duplicate record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity

    #Mock care centre response
    mock_get_care_centre_by_id.return_value = existing_care_centre
    
    result = create_centre_activity_availability(
        db=get_db_session_mock,
        centre_activity_availability_data=create_centre_activity_availability_schema,
        current_user_info=mock_supervisor_user
    )
    
    assert result.centre_activity_id == create_centre_activity_availability_schema.centre_activity_id
    assert result.created_by_id == create_centre_activity_availability_schema.created_by_id
    assert result.days_of_week == create_centre_activity_availability_schema.days_of_week
    assert result.start_time == create_centre_activity_availability_schema.start_time
    assert result.end_time == create_centre_activity_availability_schema.end_time
    assert result.start_date == create_centre_activity_availability_schema.start_date
    assert result.end_date == create_centre_activity_availability_schema.end_date

def test_create_centre_activity_availability_duplicate_found(
    get_db_session_mock,
    mock_supervisor_user,
    create_centre_activity_availability_schema,
    existing_centre_activity_availability
):
    #Mock duplicate record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_availability
    
    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=create_centre_activity_availability_schema,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Centre Activity Availability conflicts with an existing record" in exc_info.value.detail["message"]
    assert existing_centre_activity_availability.id == int(exc_info.value.detail["existing_id"])
    assert existing_centre_activity_availability.is_deleted == exc_info.value.detail["existing_is_deleted"]

@patch("app.crud.centre_activity_availability_crud.get_care_centre_by_id")
@patch("app.crud.centre_activity_availability_crud.get_centre_activity_by_id")
def test_create_centre_activity_availability_invalid_days(
    mock_get_centre_activity,
    mock_get_care_centre_by_id,
    get_db_session_mock,
    mock_supervisor_user,
    create_centre_activity_availability_schema_invalid,
    existing_centre_activity,
    existing_care_centre
):
    #Mock no duplicate record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity
    
    #Mock care centre response
    mock_get_care_centre_by_id.return_value = existing_care_centre
    
    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=create_centre_activity_availability_schema_invalid,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Care centre is closed on" in exc_info.value.detail["message"]

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
    existing_centre_activity,
    existing_care_centre
):
    #Mock centre activity availability record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_availability

    #Mock no duplicate of updated centre activity availability
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    
    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity
    
    #Mock care centre response
    mock_get_care_centre_by_id.return_value = existing_care_centre

    result = update_centre_activity_availability(
        db=get_db_session_mock,
        centre_activity_availability_data=update_centre_activity_availability_schema,
        current_user_info=mock_supervisor_user
    )
    assert result.centre_activity_id == update_centre_activity_availability_schema.centre_activity_id
    assert result.days_of_week == update_centre_activity_availability_schema.days_of_week
    assert result.start_time == update_centre_activity_availability_schema.start_time
    assert result.end_time == update_centre_activity_availability_schema.end_time
    assert result.start_date == update_centre_activity_availability_schema.start_date
    assert result.end_date == update_centre_activity_availability_schema.end_date
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
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = update_centre_activity_availability_duplicate

    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=update_centre_activity_availability_schema,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Centre Activity Availability conflicts with an existing record" in exc_info.value.detail["message"]
    assert existing_centre_activity_availability.id == int(exc_info.value.detail["existing_id"])
    assert existing_centre_activity_availability.is_deleted == exc_info.value.detail["existing_is_deleted"]

@patch("app.crud.centre_activity_availability_crud.get_care_centre_by_id")
@patch("app.crud.centre_activity_availability_crud.get_centre_activity_by_id")
def test_update_centre_activity_availability_invalid_days(
        mock_get_centre_activity,
        mock_get_care_centre_by_id,
        get_db_session_mock,
        mock_supervisor_user,
        update_centre_activity_availability_schema_invalid,
        existing_centre_activity_availability,
        existing_centre_activity,
        existing_care_centre
    ):

    #Mock centre activity availability record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_availability

    #Mock no duplicate of updated centre activity availability
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    
    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity
    
    #Mock care centre response
    mock_get_care_centre_by_id.return_value = existing_care_centre

    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_availability(
            db=get_db_session_mock,
            centre_activity_availability_data=update_centre_activity_availability_schema_invalid,
            current_user_info=mock_supervisor_user
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Care centre is closed on" in exc_info.value.detail["message"]

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

# === Role-based Access Control Tests ===
@patch("app.crud.centre_activity_availability_crud.create_centre_activity_availability")
def test_create_centre_activity_availability_role_access_success(
        mock_crud_create,
        get_db_session_mock,
        mock_supervisor_jwt,
        existing_centre_activity_availability,
        create_centre_activity_availability_schema
    ):
    mock_crud_create.return_value = existing_centre_activity_availability

    result = router_create_centre_activity_availability(
        payload=create_centre_activity_availability_schema,
        db=get_db_session_mock,
        user_and_token=(mock_supervisor_jwt, "test-token")
    )

    assert result.centre_activity_id == create_centre_activity_availability_schema.centre_activity_id
    assert result.created_by_id == create_centre_activity_availability_schema.created_by_id
    assert result.days_of_week == create_centre_activity_availability_schema.days_of_week
    assert result.start_time == create_centre_activity_availability_schema.start_time
    assert result.end_time == create_centre_activity_availability_schema.end_time
    assert result.start_date == create_centre_activity_availability_schema.start_date
    assert result.end_date == create_centre_activity_availability_schema.end_date

@pytest.mark.parametrize("mock_user_fixtures", ["mock_doctor_jwt", "mock_caregiver_jwt", "mock_admin_jwt"])
def test_create_centre_activity_availability_role_access_fail(
        get_db_session_mock,
        mock_user_fixtures,
        request,
        create_centre_activity_availability_schema
    ):
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_create_centre_activity_availability(
            payload=create_centre_activity_availability_schema,
            db=get_db_session_mock,
            user_and_token=(mock_user_roles, "test-token")
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to create a Centre Activity Availability."

@patch("app.crud.centre_activity_availability_crud.get_centre_activity_availability_by_id")
@patch("app.crud.centre_activity_availability_crud.get_care_centre_by_id")
@patch("app.crud.centre_activity_availability_crud.get_centre_activity_by_id")
def test_update_centre_activity_availability_role_access_success(
        mock_get_centre_activity,
        mock_get_care_centre_by_id,
        get_db_session_mock,
        mock_supervisor_jwt,
        existing_centre_activity_availability,
        existing_care_centre,
        existing_centre_activity,
        update_centre_activity_availability_schema
    ):
    #Mock centre activity availability record found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_availability

    #Mock no duplicate of updated centre activity availability
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = None
    
    #Mock centre activity exists
    mock_get_centre_activity.return_value = existing_centre_activity
    
    #Mock care centre response
    mock_get_care_centre_by_id.return_value = existing_care_centre
    result = router_update_centre_activity_availability(
        centre_activity_availability=update_centre_activity_availability_schema,
        db=get_db_session_mock,
        user_and_token=(mock_supervisor_jwt, "test-token")
    )
    assert result.centre_activity_id == update_centre_activity_availability_schema.centre_activity_id
    assert result.start_time == update_centre_activity_availability_schema.start_time
    assert result.end_time == update_centre_activity_availability_schema.end_time
    assert result.start_date == update_centre_activity_availability_schema.start_date
    assert result.end_date == update_centre_activity_availability_schema.end_date
    assert result.modified_by_id == update_centre_activity_availability_schema.modified_by_id
    assert result.modified_date.replace(tzinfo=timezone.utc, second=0, microsecond=0) == update_centre_activity_availability_schema.modified_date

@pytest.mark.parametrize("mock_user_fixtures", ["mock_doctor_jwt", "mock_caregiver_jwt", "mock_admin_jwt"])
def test_update_centre_activity_availability_role_access_fail(
        get_db_session_mock,
        mock_user_fixtures,
        request,
        update_centre_activity_availability_schema
    ):
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_update_centre_activity_availability(
            centre_activity_availability=update_centre_activity_availability_schema,
            db=get_db_session_mock,
            user_and_token=(mock_user_roles, "test-token")
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to update a Centre Activity Availability."

@patch("app.crud.centre_activity_availability_crud.delete_centre_activity_availability")
def test_delete_centre_activity_availability_role_access_success(
        mock_crud_delete,
        get_db_session_mock,
        mock_supervisor_jwt,
        existing_centre_activity_availability
    ):

    mock_crud_delete.return_value = existing_centre_activity_availability

    result = router_delete_centre_activity_availability(
        centre_activity_availability_id=1,
        db=get_db_session_mock,
        user_and_token=(mock_supervisor_jwt, "test-token")
    )
    assert result == existing_centre_activity_availability

@pytest.mark.parametrize("mock_user_fixtures", ["mock_doctor_jwt", "mock_caregiver_jwt", "mock_admin_jwt"])
def test_delete_centre_activity_availability_role_access_fail(
        get_db_session_mock,
        mock_user_fixtures,
        request
    ):
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_delete_centre_activity_availability(
            centre_activity_availability_id=1,
            db=get_db_session_mock,
            user_and_token=(mock_user_roles, "test-token")
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to delete a Centre Activity Availability."

@patch("app.crud.centre_activity_availability_crud.get_centre_activity_availability_by_id")
def test_get_centre_activity_availability_by_id_role_access_success(
        mock_crud_get,
        get_db_session_mock,
        mock_supervisor_jwt,
        existing_centre_activity_availability
    ):
    mock_crud_get.return_value = existing_centre_activity_availability

    result = router_get_centre_activity_availability_by_id(
        centre_activity_availability_id=1,
        db=get_db_session_mock,
        current_user=mock_supervisor_jwt
    )
    assert result == existing_centre_activity_availability
    assert result.id == 1

@pytest.mark.parametrize("mock_user_fixtures", ["mock_doctor_jwt", "mock_caregiver_jwt", "mock_admin_jwt"])
def test_get_centre_activity_availability_by_id_role_access_fail(
        get_db_session_mock,
        mock_user_fixtures,
        request    
    ):
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_get_centre_activity_availability_by_id(
            centre_activity_availability_id=1,
            db=get_db_session_mock,
            current_user=mock_user_roles
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to view a Centre Activity Availability."

@patch("app.crud.centre_activity_availability_crud.get_centre_activity_availabilities")
def test_get_centre_activity_availabilities_role_access_success(
        mock_crud_get,
        get_db_session_mock,
        mock_supervisor_jwt,
        existing_centre_activity_availabilities
    ):

    mock_crud_get.return_value = existing_centre_activity_availabilities

    result = router_get_all_centre_activity_availabilities(
        db=get_db_session_mock,
        current_user=mock_supervisor_jwt
    )
    for actual_data, expected_data in zip(result, existing_centre_activity_availabilities):
        assert actual_data.id == expected_data.id
        assert actual_data.centre_activity_id == expected_data.centre_activity_id
        assert actual_data.is_deleted == expected_data.is_deleted
        assert actual_data.start_time == expected_data.start_time
        assert actual_data.end_time == expected_data.end_time
        assert actual_data.start_date == expected_data.start_date
        assert actual_data.end_date == expected_data.end_date
        assert actual_data.created_by_id == expected_data.created_by_id
        assert actual_data.modified_by_id == expected_data.modified_by_id

@pytest.mark.parametrize("mock_user_fixtures", ["mock_doctor_jwt", "mock_caregiver_jwt", "mock_admin_jwt"])
def test_get_centre_activity_availabilities_role_access_fail(
        get_db_session_mock,
        mock_user_fixtures,
        request    
    ):
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_get_all_centre_activity_availabilities(
             db=get_db_session_mock,
            current_user=mock_user_roles
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to view Centre Activity Availabilities."

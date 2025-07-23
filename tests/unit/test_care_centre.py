import pytest
from unittest.mock import MagicMock, patch
import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import ValidationError
import conftest
from app.models.care_centre_model import CareCentre as CareCentreModel
from app.schemas.care_centre_schema import CareCentreCreate, CareCentreUpdate, CareCentreResponse
from app.crud.care_centre_crud import (
    create_care_centre,
    get_care_centre_by_id,
    update_care_centre,
    delete_care_centre,
    get_care_centres,
)
# For role tests
from app.routers.care_centre_router import (
    create_care_centre as router_create_care_centre,
    list_care_centres as router_list_care_centres,
    get_care_centre_by_id as router_get_care_centre_by_id,
    update_care_centre as router_update_care_centre,
    delete_care_centre as router_delete_care_centre,
)

@pytest.fixture
def create_care_centre_schema(base_care_centre_data):
    return CareCentreCreate(**base_care_centre_data)

@pytest.fixture
def update_care_centre_schema(base_care_centre_data_list):
    return CareCentreUpdate(**base_care_centre_data_list[1])  # Use the second item for update

# ===== Validator tests =======
@pytest.mark.parametrize(
        "override_fields, expected_error",
        [
            # Invalid Country Code
            ({"country_code": "SG"}, "Invalid country code: SG. Must be 3 uppercase letters (ISO 3166-1 alpha-3)"),

            # Invalid working_hours: missing_days
            ({"working_hours": {"monday": {"open": "09:00", "close": "17:00"}}},
             "Missing working hours for: ['friday', 'saturday', 'sunday', 'thursday', 'tuesday', 'wednesday']"),
#
            # Invalid working_hours: open/close mismatch
            ({"working_hours": {
                "monday": {"open": None, "close": "17:00"},
                "tuesday": {"open": "09:00", "close": None},
                "wednesday": {"open": "09:00", "close": "17:00"},
                "thursday": {"open": "09:00", "close": "17:00"},
                "friday": {"open": "09:00", "close": "17:00"},
                "saturday": {"open": None, "close": None},
                "sunday": {"open": None, "close": None}}},
             "working_hours errors:\n"
             "Both open and close must be specified or null for monday\n"
             "Both open and close must be specified or null for tuesday"),

            # Invalid working_hours: invalid time format
            ({"working_hours": {
                "monday": {"open": "9:00", "close": "17:00"},
                "tuesday": {"open": "09:00", "close": "24:00"},
                "wednesday": {"open": "09:00", "close": "17:00"},
                "thursday": {"open": "09:00", "close": "17:00"},
                "friday": {"open": "09:00", "close": "17:00"},
                "saturday": {"open": None, "close": None},
                "sunday": {"open": None, "close": None}}},
            "working_hours errors:\n"
            "Invalid time format for open on monday: 9:00\n"
            "Invalid time format for close on tuesday: 24:00"),

            # Invalid working_hours: close time before open time
            ({"working_hours": {
                "monday": {"open": "17:00", "close": "09:00"},
                "tuesday": {"open": "09:00", "close": "17:00"},
                "wednesday": {"open": "09:00", "close": "17:00"},
                "thursday": {"open": "09:00", "close": "17:00"},
                "friday": {"open": "09:00", "close": "17:00"},
                "saturday": {"open": None, "close": None},
                "sunday": {"open": None, "close": None}}},
             "Close time must be after open time for monday (17:00 >= 09:00)"),
        ]
)
@pytest.mark.parametrize("schema_class", [CareCentreCreate, CareCentreUpdate])
def test_care_centre_schema_validation_fails(base_care_centre_data, schema_class, override_fields, expected_error):
    """Test that CareCentreCreate schema validation fails with invalid data."""
    
    data = {**base_care_centre_data, **override_fields}

    with pytest.raises(ValidationError) as exc_info:
        schema_class(**data)

    assert expected_error in str(exc_info.value)


# ===== CREATE tests ======
def test_create_care_centre_success(get_db_session_mock, mock_supervisor_user,
                                    create_care_centre_schema):
    """ Creates when no duplicate Care Centre exists"""

    # No duplicate Care Centre
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None 
    
    result = create_care_centre(
        db=get_db_session_mock,
        care_centre_data=create_care_centre_schema,
        current_user_info=mock_supervisor_user
    )

    assert result.name == create_care_centre_schema.name
    assert result.country_code == create_care_centre_schema.country_code
    assert result.address == create_care_centre_schema.address
    assert result.postal_code == create_care_centre_schema.postal_code
    assert result.contact_no == create_care_centre_schema.contact_no
    assert result.email == create_care_centre_schema.email
    assert result.no_of_devices_avail == create_care_centre_schema.no_of_devices_avail
    assert result.working_hours == create_care_centre_schema.working_hours
    assert result.remarks == create_care_centre_schema.remarks
    assert result.created_by_id == mock_supervisor_user["id"]


def test_create_care_centre_duplicate_fail(get_db_session_mock, mock_supervisor_user,
                                           create_care_centre_schema, existing_care_centre):
        """ Raises HTTPException when duplicate Care Centre exists"""

        # Duplicate Care Centre exists
        get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = existing_care_centre

        with pytest.raises(HTTPException) as exc_info:
             create_care_centre(
                  db=get_db_session_mock,
                  care_centre_data=create_care_centre_schema,
                    current_user_info=mock_supervisor_user
             )
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == {
            "message": "Care Centre with these attributes already exists or deleted",
            "existing_id": str(existing_care_centre.id),
            "existing_is_deleted": existing_care_centre.is_deleted
        }


# ====== GET tests ======
def test_get_care_centre_by_id_success(get_db_session_mock, existing_care_centre):
    """ Successfully retrieves Care Centre by ID """

    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = existing_care_centre

    result = get_care_centre_by_id(db=get_db_session_mock, care_centre_id=existing_care_centre.id)

    assert result.id == existing_care_centre.id
    assert result.name == existing_care_centre.name
    assert result.country_code == existing_care_centre.country_code
    assert result.address == existing_care_centre.address
    assert result.postal_code == existing_care_centre.postal_code
    assert result.contact_no == existing_care_centre.contact_no
    assert result.email == existing_care_centre.email
    assert result.no_of_devices_avail == existing_care_centre.no_of_devices_avail
    assert result.working_hours == existing_care_centre.working_hours
    assert result.remarks == existing_care_centre.remarks

def test_get_care_centre_by_id_not_found(get_db_session_mock):
    """ Raises HTTPException when Care Centre not found """

    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_care_centre_by_id(db=get_db_session_mock, care_centre_id=999)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Care Centre not found"

def test_get_care_centres_success(get_db_session_mock, existing_care_centres):
    """ Successfully retrieves list of Care Centres """

    get_db_session_mock.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = existing_care_centres

    result = get_care_centres(db=get_db_session_mock, include_deleted=False, skip=0, limit=100)

    assert len(result) == len(existing_care_centres)
    for i, centre in enumerate(result):
        assert centre.id == existing_care_centres[i].id
        assert centre.name == existing_care_centres[i].name

def test_get_care_centres_fail(get_db_session_mock):
    """ Raises HTTPException when database query fails """

    get_db_session_mock.query.return_value.filter.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        get_care_centres(
            db=get_db_session_mock, 
            include_deleted=False, 
            skip=0, limit=100
            )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "No Care Centres found"

#===== UPDATE tests ======
def test_update_care_centre_success(get_db_session_mock, mock_supervisor_user, 
                                    update_care_centre_schema, existing_care_centre):
    """ Successfully updates Care Centre """

    # Valid existing Care Centre
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_care_centre
    # No duplicate Care Centre
    get_db_session_mock.query.return_value.filter.return_value.filter_by.return_value.first.return_value = None
    
    result = update_care_centre(
        db=get_db_session_mock,
        care_centre_data=update_care_centre_schema,
        current_user_info=mock_supervisor_user
    )

    # Fields that should not be updated
    assert result.id == existing_care_centre.id
    assert result.created_date == existing_care_centre.created_date

    assert result.name == update_care_centre_schema.name
    assert result.country_code == update_care_centre_schema.country_code
    assert result.address == update_care_centre_schema.address
    assert result.postal_code == update_care_centre_schema.postal_code
    assert result.contact_no == update_care_centre_schema.contact_no
    assert result.email == update_care_centre_schema.email
    assert result.no_of_devices_avail == update_care_centre_schema.no_of_devices_avail
    assert result.working_hours == update_care_centre_schema.working_hours
    assert result.remarks == update_care_centre_schema.remarks
    assert result.modified_by_id == mock_supervisor_user["id"]
    assert result.modified_date is not None

def test_update_care_centre_not_found_fail(get_db_session_mock, mock_supervisor_user, update_care_centre_schema):
    """ Raises HTTPException when Care Centre not found """

    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        update_care_centre(
            db=get_db_session_mock,
            care_centre_data=update_care_centre_schema,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Care Centre not found"

def test_update_care_centre_duplicate_fail(get_db_session_mock, mock_supervisor_user, 
                                           update_care_centre_schema, existing_care_centre):
    """ Raises HTTPException when duplicate Care Centre exists """

    # Valid existing Care Centre
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_care_centre

    # Update creates a duplicate Care Centre
    get_db_session_mock.query.return_value.filter.return_value.filter_by.return_value.first.return_value = existing_care_centre

    with pytest.raises(HTTPException) as exc_info:
        update_care_centre(
            db=get_db_session_mock,
            care_centre_data=update_care_centre_schema,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == {
        "message": "Care Centre with these attributes already exists or deleted",
        "existing_id": str(existing_care_centre.id),
        "existing_is_deleted": existing_care_centre.is_deleted
    }

# ====== DELETE tests ======
def test_delete_care_centre_success(get_db_session_mock, mock_supervisor_user, existing_care_centre):
    """ Successfully deletes Care Centre """

    # Valid existing Care Centre
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_care_centre

    result = delete_care_centre(
        db=get_db_session_mock,
        care_centre_id=existing_care_centre.id,
        current_user_info=mock_supervisor_user
    )

    assert result.id == existing_care_centre.id
    assert result.is_deleted is True
    assert result.modified_by_id == mock_supervisor_user["id"]
    assert result.modified_date is not None

def test_delete_care_centre_not_found_fail(get_db_session_mock, mock_supervisor_user):
    """ Raises HTTPException when Care Centre not found """

    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        delete_care_centre(
            db=get_db_session_mock,
            care_centre_id=999,
            current_user_info=mock_supervisor_user
        )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Care Centre not found or already deleted"


# === Role-based Access Control Tests ===
@patch("app.crud.care_centre_crud.create_care_centre")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_admin_jwt"])
def test_create_care_centre_role_access(mock_crud_create_care_centre, get_db_session_mock, mock_user_fixtures, request, create_care_centre_schema):
    """ Tests that only Supervisor and Admin can create Care Centre """
    
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_create_care_centre.return_value = CareCentreModel(**create_care_centre_schema.model_dump())

    result = router_create_care_centre(
        payload=create_care_centre_schema,
        db=get_db_session_mock,
        current_user=mock_user_roles
    )

    assert result.name == create_care_centre_schema.name
    assert result.country_code == create_care_centre_schema.country_code

def test_create_care_centre_role_access_fail(get_db_session_mock, mock_doctor_jwt, create_care_centre_schema):
    """ Fails when non-supervisor/admin tries to create Care Centre """

    #mock_crud_create_care_centre.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        router_create_care_centre(
            payload=create_care_centre_schema,
            db=get_db_session_mock,
            current_user=mock_doctor_jwt
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to create a Care Centre."

@patch("app.crud.care_centre_crud.get_care_centres")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_admin_jwt"])
def test_list_care_centres_role_access_success(mock_crud_get_care_centres, get_db_session_mock, existing_care_centres, 
                                               mock_user_fixtures, request):
    """ Tests that Supervisor and Admin can list Care Centres """
    
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get_care_centres.return_value = existing_care_centres

    result = router_list_care_centres(
        db=get_db_session_mock,
        current_user=mock_user_roles
    )

    assert len(result) == len(existing_care_centres)

def test_list_care_centres_role_access_fail(get_db_session_mock, mock_doctor_jwt):
    """ Fails when non-supervisor/admin tries to list Care Centres """

    with pytest.raises(HTTPException) as exc_info:
        router_list_care_centres(
            db=get_db_session_mock,
            current_user=mock_doctor_jwt
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to view Care Centres."

@patch("app.crud.care_centre_crud.get_care_centre_by_id")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_admin_jwt"])
def test_get_care_centre_by_id_role_access_success(mock_crud_get_care_centre_by_id, get_db_session_mock, existing_care_centres, 
                                                   mock_user_fixtures, request):
    """ Tests that Supervisor and Admin can get Care Centre by ID """
    
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get_care_centre_by_id.return_value = existing_care_centres[0]

    result = router_get_care_centre_by_id(
        care_centre_id=existing_care_centres[0].id,
        db=get_db_session_mock,
        current_user=mock_user_roles
    )

    assert result.id == existing_care_centres[0].id

def test_get_care_centre_by_id_role_access_fail(get_db_session_mock, mock_doctor_jwt):
    """ Fails when non-supervisor/admin tries to get Care Centre by ID """

    with pytest.raises(HTTPException) as exc_info:
        router_get_care_centre_by_id(
            care_centre_id=999,
            db=get_db_session_mock,
            current_user=mock_doctor_jwt
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to view this Care Centre."

@patch("app.crud.care_centre_crud.update_care_centre")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_admin_jwt"])
def test_update_care_centre_role_access_success(mock_crud_update_care_centre,
                                                get_db_session_mock, update_care_centre_schema, existing_care_centres, 
                                                mock_user_fixtures, request):
    """ Tests that Supervisor and Admin can update Care Centre """
    
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_update_care_centre.return_value = CareCentreModel(**update_care_centre_schema.model_dump())

    result = router_update_care_centre(
        payload=update_care_centre_schema,
        db=get_db_session_mock,
        current_user=mock_user_roles
    )

    assert result.id == existing_care_centres[1].id
    assert result.name == update_care_centre_schema.name

def test_update_care_centre_role_access_fail(get_db_session_mock, mock_doctor_jwt, update_care_centre_schema):
    """ Fails when non-supervisor/admin tries to update Care Centre """

    with pytest.raises(HTTPException) as exc_info:
        router_update_care_centre(
            payload=update_care_centre_schema,
            db=get_db_session_mock,
            current_user=mock_doctor_jwt
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to update a Care Centre."

@patch("app.crud.care_centre_crud.delete_care_centre")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_admin_jwt"])
def test_delete_care_centre_role_access_success(mock_crud_delete_care_centre, 
                                                get_db_session_mock, existing_care_centres, 
                                                mock_user_fixtures, request):
    """ Tests that Supervisor and Admin can delete Care Centre """
    
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_delete_care_centre.return_value = existing_care_centres[0]

    result = router_delete_care_centre(
        care_centre_id=existing_care_centres[0].id,
        db=get_db_session_mock,
        current_user=mock_user_roles
    )

    assert result.id == existing_care_centres[0].id

def test_delete_care_centre_role_access_fail(get_db_session_mock, mock_doctor_jwt):
    """ Fails when non-supervisor/admin tries to delete Care Centre """

    with pytest.raises(HTTPException) as exc_info:
        router_delete_care_centre(
            care_centre_id=999,
            db=get_db_session_mock,
            current_user=mock_doctor_jwt
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to delete a Care Centre."
import pytest
from unittest.mock import MagicMock, patch
import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import ValidationError
from app.models.centre_activity_preference_model import CentreActivityPreference as CentreActivityPreferenceModel
from app.schemas.centre_activity_preference_schema import CentreActivityPreferenceCreate, CentreActivityPreferenceUpdate, CentreActivityPreferenceResponse
from app.crud.centre_activity_preference_crud import (
    create_centre_activity_preference,
    get_centre_activity_preference_by_id,
    get_centre_activity_preferences_by_patient_id,
    get_centre_activity_preferences,
    update_centre_activity_preference_by_id,
    delete_centre_activity_preference_by_id,
)
# For role tests
from app.routers.centre_activity_preference_router import (
    create_centre_activity_preference as router_create_centre_activity_preference,
    get_centre_activity_preferences as router_get_centre_activity_preferences,
    get_centre_activity_preference_by_id as router_get_centre_activity_preference_by_id,
    get_centre_activity_preferences_by_patient_id as router_get_centre_activity_preferences_by_patient_id,
    update_centre_activity_preference_by_id as router_update_centre_activity_preference_by_id,
    delete_centre_activity_preference_by_id as router_delete_centre_activity_preference_by_id,
)


@pytest.fixture
def create_centre_activity_preference_schema(base_centre_activity_preference_data):
    return CentreActivityPreferenceCreate(**base_centre_activity_preference_data)

@pytest.fixture
def update_centre_activity_preference_schema(base_centre_activity_preference_data_list):
    return CentreActivityPreferenceUpdate(**base_centre_activity_preference_data_list[1])


# ===== CREATE tests ======
@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_by_id")
def test_create_centre_activity_preference_success(mock_get_centre_activity, mock_get_patient, mock_get_patient_allocation,
                                                  get_db_session_mock, mock_caregiver_user, 
                                                  create_centre_activity_preference_schema,
                                                 existing_activity, mock_patient_service_response, mock_allocation_response):
    """Creates Centre Activity Preference when all conditions are met"""

    # Mock no existing preference
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None

    # Mock centre activity exists
    mock_get_centre_activity.return_value = existing_activity
    
    # Mock patient exists and user has access
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_allocation_response
    
    result = create_centre_activity_preference(
        db=get_db_session_mock,
        centre_activity_preference_data=create_centre_activity_preference_schema,
        current_user_info=mock_caregiver_user,
    )

    assert result.centre_activity_id == create_centre_activity_preference_schema.centre_activity_id
    assert result.patient_id == create_centre_activity_preference_schema.patient_id
    assert result.is_like == create_centre_activity_preference_schema.is_like
    assert result.created_by_id == mock_caregiver_user["id"]
    
    get_db_session_mock.add.assert_called_once()
    get_db_session_mock.commit.assert_called_once()

@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_by_id")
def test_create_centre_activity_preference_duplicate_fail(mock_get_centre_activity, mock_get_patient,
                                                        mock_get_patient_allocation, get_db_session_mock,
                                                        mock_caregiver_user, create_centre_activity_preference_schema,
                                                        existing_activity, existing_centre_activity_preference,
                                                        mock_patient_service_response, mock_allocation_response):
    """Raises HTTPException when duplicate Centre Activity Preference exists"""
    mock_get_centre_activity.return_value = existing_activity
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_allocation_response
    
    # Mock existing preference
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_preference

    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_preference(
            db=get_db_session_mock,
            centre_activity_preference_data=create_centre_activity_preference_schema,
            current_user_info=mock_caregiver_user,
        )
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Centre Activity Preference with these attributes already exists" in str(exc_info.value.detail)

@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_by_id")
def test_create_centre_activity_preference_centre_activity_not_found_fail(mock_get_centre_activity, mock_get_patient, mock_get_patient_allocation,
                                                                        get_db_session_mock, mock_patient_service_response,
                                                                        mock_allocation_response, mock_caregiver_user,
                                                                        create_centre_activity_preference_schema):
    """Raises HTTPException when Centre Activity not found"""

    # No duplicate Centre activity preference 
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    # Mock centre activity not found
    mock_get_centre_activity.side_effect = HTTPException(status_code=404, detail="Centre Activity not found")

    # Valid patient id
    mock_get_patient.return_value = mock_patient_service_response

    # Valid allocation
    mock_get_patient_allocation.return_value = mock_allocation_response


    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_preference(
            db=get_db_session_mock,
            centre_activity_preference_data=create_centre_activity_preference_schema,
            current_user_info=mock_caregiver_user,
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Centre Activity not found"

@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_by_id")
def test_create_centre_activity_preference_patient_not_found_fail(mock_get_centre_activity, mock_get_patient,
                                                                mock_get_patient_allocation, get_db_session_mock, mock_caregiver_user,
                                                                create_centre_activity_preference_schema,
                                                                existing_activity):
    """Raises HTTPException when Patient not found"""
    mock_get_centre_activity.return_value = existing_activity
    
    # Mock patient not found
    mock_patient_response = MagicMock()
    mock_patient_response.status_code = 404
    mock_get_patient.return_value = mock_patient_response
    
    # Mock patient allocation (even though patient check should fail first)
    mock_allocation_response = MagicMock()
    mock_allocation_response.status_code = 200
    mock_get_patient_allocation.return_value = mock_allocation_response
    
    # Mock no existing preference
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_preference(
            db=get_db_session_mock,
            centre_activity_preference_data=create_centre_activity_preference_schema,
            current_user_info=mock_caregiver_user,
        )
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Patient not found or not accessible"

@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_by_id")
def test_create_centre_activity_preference_unauthorized_caregiver_fail(mock_get_centre_activity, mock_get_patient,
                                                                      mock_get_patient_allocation, get_db_session_mock,
                                                                      mock_caregiver_user, create_centre_activity_preference_schema,
                                                                      existing_activity, mock_patient_service_response):
    """Raises HTTPException when caregiver is not assigned to patient"""
    mock_get_centre_activity.return_value = existing_activity
    mock_get_patient.return_value = mock_patient_service_response
    
    # Mock patient allocation with different caregiver
    unauthorized_allocation_response = MagicMock()
    unauthorized_allocation_response.status_code = 200
    unauthorized_allocation_response.json.return_value = {
        "patientId": 1,
        "caregiverId": "999",  # Different caregiver
        "supervisorId": "2"
    }
    mock_get_patient_allocation.return_value = unauthorized_allocation_response
    
    # Mock no existing preference
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_preference(
            db=get_db_session_mock,
            centre_activity_preference_data=create_centre_activity_preference_schema,
            current_user_info=mock_caregiver_user,
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "You do not have permission to create a Centre Activity Preference" in exc_info.value.detail

# ===== GET tests ======
def test_get_centre_activity_preference_by_id_success(get_db_session_mock, existing_centre_activity_preference):
    """Successfully retrieves Centre Activity Preference by ID"""
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = existing_centre_activity_preference

    result = get_centre_activity_preference_by_id(
        db=get_db_session_mock, 
        centre_activity_preference_id=existing_centre_activity_preference.id
    )

    assert result.id == existing_centre_activity_preference.id
    assert result.centre_activity_id == existing_centre_activity_preference.centre_activity_id
    assert result.patient_id == existing_centre_activity_preference.patient_id
    assert result.is_like == existing_centre_activity_preference.is_like

def test_get_centre_activity_preference_by_id_not_found_fail(get_db_session_mock):
    """Raises HTTPException when Centre Activity Preference not found"""
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_centre_activity_preference_by_id(db=get_db_session_mock, centre_activity_preference_id=999)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Centre Activity Preference not found"

def test_get_centre_activity_preferences_by_patient_id_success(get_db_session_mock, existing_centre_activity_preferences):
    """Successfully retrieves Centre Activity Preferences by Patient ID"""
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = existing_centre_activity_preferences

    result = get_centre_activity_preferences_by_patient_id(
        db=get_db_session_mock, 
        patient_id=1,
        include_deleted=False,
        skip=0,
        limit=100
    )

    assert len(result) == len(existing_centre_activity_preferences)
    for actual, expected in zip(result, existing_centre_activity_preferences):
        assert actual.id == expected.id
        assert actual.patient_id == expected.patient_id

def test_get_centre_activity_preferences_by_patient_id_not_found_fail(get_db_session_mock):
    """Raises HTTPException when no Centre Activity Preferences found for Patient"""
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_centre_activity_preferences_by_patient_id(
            db=get_db_session_mock,
            patient_id=999,
            include_deleted=False,
            skip=0,
            limit=100
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "No Centre Activity Preferences found for this Patient"

def test_get_centre_activity_preferences_success(get_db_session_mock, existing_centre_activity_preferences):
    """Successfully retrieves all Centre Activity Preferences"""
    get_db_session_mock.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = existing_centre_activity_preferences

    result = get_centre_activity_preferences(
        db=get_db_session_mock,
        include_deleted=False,
        skip=0,
        limit=100
    )

    assert len(result) == len(existing_centre_activity_preferences)
    for actual, expected in zip(result, existing_centre_activity_preferences):
        assert actual.id == expected.id
        assert actual.centre_activity_id == expected.centre_activity_id

# ===== UPDATE tests ======
@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_by_id")
def test_update_centre_activity_preference_success(mock_get_centre_activity, mock_get_patient,
                                                  mock_get_patient_allocation, get_db_session_mock,
                                                  mock_caregiver_user, update_centre_activity_preference_schema,
                                                  existing_activity, existing_centre_activity_preference,
                                                  mock_patient_service_response, mock_allocation_response):
    """Successfully updates Centre Activity Preference"""
    mock_get_centre_activity.return_value = existing_activity
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_allocation_response  # Use proper allocation response
    
    # Check if preference exists
    mock_filter_exists = MagicMock()
    mock_filter_exists.first.return_value = existing_centre_activity_preference
    
    # Check for duplicates - this uses db.query().filter().filter().first()
    mock_filter_duplicates = MagicMock()
    mock_filter_duplicates_chain = MagicMock()
    mock_filter_duplicates_chain.first.return_value = None  # No duplicates
    mock_filter_duplicates.filter.return_value = mock_filter_duplicates_chain
    
    # Get preference for final update
    mock_filter_update = MagicMock()
    mock_filter_update.first.return_value = existing_centre_activity_preference
    
    # Create separate query objects that return different filter chains
    def mock_query_side_effect(model):
        if hasattr(mock_query_side_effect, 'call_count'):
            mock_query_side_effect.call_count += 1
        else:
            mock_query_side_effect.call_count = 1
            
        mock_query = MagicMock()
        if mock_query_side_effect.call_count == 1:
            mock_query.filter.return_value = mock_filter_exists
        elif mock_query_side_effect.call_count == 2:
            mock_query.filter.return_value = mock_filter_duplicates
        else:
            mock_query.filter.return_value = mock_filter_update
        return mock_query
    
    get_db_session_mock.query.side_effect = mock_query_side_effect

    result = update_centre_activity_preference_by_id(
        db=get_db_session_mock,
        centre_activity_preference_data=update_centre_activity_preference_schema,
        current_user_info=mock_caregiver_user,
    )

    assert result.centre_activity_id == update_centre_activity_preference_schema.centre_activity_id
    assert result.patient_id == update_centre_activity_preference_schema.patient_id
    assert result.is_like == update_centre_activity_preference_schema.is_like
    assert result.modified_by_id == mock_caregiver_user["id"]
    assert result.modified_date is not None
    
    get_db_session_mock.commit.assert_called_once()

@patch("app.crud.centre_activity_preference_crud.get_centre_activity_by_id")
def test_update_centre_activity_preference_not_found_fail(mock_get_centre_activity, get_db_session_mock,
                                                        mock_caregiver_user, update_centre_activity_preference_schema,
                                                        existing_activity):
    """Raises HTTPException when Centre Activity Preference not found"""
    mock_get_centre_activity.return_value = existing_activity
    
    # Mock preference not found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_preference_by_id(
            db=get_db_session_mock,
            centre_activity_preference_data=update_centre_activity_preference_schema,
            current_user_info=mock_caregiver_user,
        )
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Centre Activity Preference not found"

@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_by_id")
def test_update_centre_activity_preference_duplicate_fail(mock_get_centre_activity, mock_get_patient,
                                                         mock_get_patient_allocation, get_db_session_mock,
                                                         mock_caregiver_user, update_centre_activity_preference_schema,
                                                        existing_activity, existing_centre_activity_preference,
                                                        mock_patient_service_response, mock_allocation_response):
    """Raises HTTPException when duplicate Centre Activity Preference exists"""
    mock_get_centre_activity.return_value = existing_activity
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_allocation_response
    
    # Mock existing preference and duplicate
    duplicate_preference = MagicMock()
    duplicate_preference.id = 999
    duplicate_preference.is_deleted = False  

    # Centre activity preference exists
    mock_filter_exists = MagicMock()
    mock_filter_exists.first.return_value = existing_centre_activity_preference
    
    # Duplicate Centre Activity Preference found
    mock_filter_duplicates = MagicMock()
    mock_filter_by_duplicates = MagicMock()
    mock_filter_by_duplicates.first.return_value = duplicate_preference 
    mock_filter_duplicates.filter_by.return_value = mock_filter_by_duplicates
    
    # Create query mock that handles the sequence
    def mock_query_side_effect(model):
        if hasattr(mock_query_side_effect, 'call_count'):
            mock_query_side_effect.call_count += 1
        else:
            mock_query_side_effect.call_count = 1
            
        mock_query = MagicMock()
        if mock_query_side_effect.call_count == 1:
            # First call: check if preference exists
            mock_query.filter.return_value = mock_filter_exists
        elif mock_query_side_effect.call_count == 2:
            # Second call: check for duplicates - finds duplicate
            mock_query.filter.return_value = mock_filter_duplicates
        return mock_query
    
    get_db_session_mock.query.side_effect = mock_query_side_effect

    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_preference_by_id(
            db=get_db_session_mock,
            centre_activity_preference_data=update_centre_activity_preference_schema,
            current_user_info=mock_caregiver_user,
        )
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Centre Activity Preference with these attributes already exists" in str(exc_info.value.detail)

# ===== DELETE tests ======
def test_delete_centre_activity_preference_success(get_db_session_mock, mock_caregiver_user, existing_centre_activity_preference):
    """Successfully deletes (soft delete) Centre Activity Preference"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_preference

    result = delete_centre_activity_preference_by_id(
        centre_activity_preference_id=existing_centre_activity_preference.id,
        db=get_db_session_mock,
        current_user_info=mock_caregiver_user,
    )

    assert result.is_deleted == True
    assert result.modified_by_id == mock_caregiver_user["id"]
    assert result.modified_date is not None
    
    get_db_session_mock.commit.assert_called_once()

def test_delete_centre_activity_preference_not_found_fail(get_db_session_mock, mock_caregiver_user):
    """Raises HTTPException when Centre Activity Preference not found"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        delete_centre_activity_preference_by_id(
            centre_activity_preference_id=999,
            db=get_db_session_mock,
            current_user_info=mock_caregiver_user,
        )
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Centre Activity Preference not found or deleted"

# === Role-based Access Control Tests ===
@patch("app.crud.centre_activity_preference_crud.create_centre_activity_preference")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_caregiver_jwt"])
def test_create_centre_activity_preference_role_access_success(mock_crud_create, get_db_session_mock, 
                                                             mock_user_fixtures, request, 
                                                             create_centre_activity_preference_schema):
    """Tests that Supervisor and Caregiver can create Centre Activity Preference"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    mock_result = MagicMock()
    mock_result.centre_activity_id = create_centre_activity_preference_schema.centre_activity_id
    mock_result.patient_id = create_centre_activity_preference_schema.patient_id
    mock_result.is_like = create_centre_activity_preference_schema.is_like
    mock_crud_create.return_value = mock_result

    result = router_create_centre_activity_preference(
        payload=create_centre_activity_preference_schema,
        db=get_db_session_mock,
        current_user=mock_user_roles,
        token="test-token"
    )

    assert result.centre_activity_id == create_centre_activity_preference_schema.centre_activity_id
    assert result.patient_id == create_centre_activity_preference_schema.patient_id

def test_create_centre_activity_preference_role_access_fail(get_db_session_mock, mock_doctor_jwt, create_centre_activity_preference_schema):
    """Fails when non-supervisor/caregiver tries to create Centre Activity Preference"""
    with pytest.raises(HTTPException) as exc_info:
        router_create_centre_activity_preference(
            payload=create_centre_activity_preference_schema,
            db=get_db_session_mock,
            current_user=mock_doctor_jwt,
            token="test-token"
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to create a Centre Activity Preference"

@patch("app.crud.centre_activity_preference_crud.get_centre_activity_preferences")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_caregiver_jwt"])
def test_get_centre_activity_preferences_role_access_success(mock_crud_get, get_db_session_mock, 
                                                           existing_centre_activity_preferences,
                                                           mock_user_fixtures, request):
    """Tests that Supervisor and Caregiver can list Centre Activity Preferences"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get.return_value = existing_centre_activity_preferences

    result = router_get_centre_activity_preferences(
        db=get_db_session_mock,
        current_user=mock_user_roles
    )

    assert len(result) == len(existing_centre_activity_preferences)

def test_get_centre_activity_preferences_role_access_fail(get_db_session_mock, mock_doctor_jwt):
    """Fails when non-supervisor/caregiver tries to list Centre Activity Preferences"""
    with pytest.raises(HTTPException) as exc_info:
        router_get_centre_activity_preferences(
            db=get_db_session_mock,
            current_user=mock_doctor_jwt
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to view Centre Activity Preferences"

@patch("app.crud.centre_activity_preference_crud.get_centre_activity_preference_by_id")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_caregiver_jwt"])
def test_get_centre_activity_preference_by_id_role_access_success(mock_crud_get, get_db_session_mock,
                                                                existing_centre_activity_preferences,
                                                                mock_user_fixtures, request):
    """Tests that Supervisor and Caregiver can get Centre Activity Preference by ID"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get.return_value = existing_centre_activity_preferences[0]

    result = router_get_centre_activity_preference_by_id(
        centre_activity_preference_id=existing_centre_activity_preferences[0].id,
        db=get_db_session_mock,
        current_user=mock_user_roles
    )

    assert result.id == existing_centre_activity_preferences[0].id

def test_get_centre_activity_preference_by_id_role_access_fail(get_db_session_mock, mock_doctor_jwt):
    """Fails when non-supervisor/caregiver tries to get Centre Activity Preference by ID"""
    with pytest.raises(HTTPException) as exc_info:
        router_get_centre_activity_preference_by_id(
            centre_activity_preference_id=1,
            db=get_db_session_mock,
            current_user=mock_doctor_jwt
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to view this Centre Activity Preference"

@patch("app.crud.centre_activity_preference_crud.get_centre_activity_preferences_by_patient_id")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_caregiver_jwt"])
def test_get_centre_activity_preferences_by_patient_id_role_access_success(mock_crud_get, get_db_session_mock,
                                                                         existing_centre_activity_preferences,
                                                                         mock_user_fixtures, request):
    """Tests that Supervisor and Caregiver can get Centre Activity Preferences by Patient ID"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get.return_value = existing_centre_activity_preferences

    result = router_get_centre_activity_preferences_by_patient_id(
        patient_id=1,
        db=get_db_session_mock,
        current_user=mock_user_roles
    )

    assert len(result) == len(existing_centre_activity_preferences)

def test_get_centre_activity_preferences_by_patient_id_role_access_fail(get_db_session_mock, mock_doctor_jwt):
    """Fails when non-supervisor/caregiver tries to get Centre Activity Preferences by Patient ID"""
    with pytest.raises(HTTPException) as exc_info:
        router_get_centre_activity_preferences_by_patient_id(
            patient_id=1,
            db=get_db_session_mock,
            current_user=mock_doctor_jwt
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to view Centre Activity Preferences for this Patient"

@patch("app.crud.centre_activity_preference_crud.update_centre_activity_preference_by_id")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_caregiver_jwt"])
def test_update_centre_activity_preference_role_access_success(mock_crud_update, get_db_session_mock,
                                                             update_centre_activity_preference_schema,
                                                             existing_centre_activity_preferences,
                                                             mock_user_fixtures, request):
    """Tests that Supervisor and Caregiver can update Centre Activity Preference"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    # Existing Centre Activity Preference
    mock_result = existing_centre_activity_preferences[0]
    mock_result.centre_activity_id = update_centre_activity_preference_schema.centre_activity_id
    mock_result.patient_id = update_centre_activity_preference_schema.patient_id
    mock_result.is_like = update_centre_activity_preference_schema.is_like
    mock_crud_update.return_value = mock_result

    result = router_update_centre_activity_preference_by_id(
        payload=update_centre_activity_preference_schema,
        db=get_db_session_mock,
        current_user=mock_user_roles,
        token="test-token"
    )

    assert result.centre_activity_id == update_centre_activity_preference_schema.centre_activity_id
    assert result.patient_id == update_centre_activity_preference_schema.patient_id

def test_update_centre_activity_preference_role_access_fail(get_db_session_mock, mock_doctor_jwt, update_centre_activity_preference_schema):
    """Fails when non-supervisor/caregiver tries to update Centre Activity Preference"""
    with pytest.raises(HTTPException) as exc_info:
        router_update_centre_activity_preference_by_id(
            payload=update_centre_activity_preference_schema,
            db=get_db_session_mock,
            current_user=mock_doctor_jwt,
            token="test-token"
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to update this Centre Activity Preference"

@patch("app.crud.centre_activity_preference_crud.delete_centre_activity_preference_by_id")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_caregiver_jwt"])
def test_delete_centre_activity_preference_role_access_success(mock_crud_delete, get_db_session_mock,
                                                             existing_centre_activity_preferences,
                                                             mock_user_fixtures, request):
    """Tests that Supervisor and Caregiver can delete Centre Activity Preference"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_delete.return_value = existing_centre_activity_preferences[0]

    result = router_delete_centre_activity_preference_by_id(
        centre_activity_preference_id=existing_centre_activity_preferences[0].id,
        db=get_db_session_mock,
        current_user=mock_user_roles,
        token="test-token"
    )

    assert result.id == existing_centre_activity_preferences[0].id

def test_delete_centre_activity_preference_role_access_fail(get_db_session_mock, mock_doctor_jwt):
    """Fails when non-supervisor/caregiver tries to delete Centre Activity Preference"""
    with pytest.raises(HTTPException) as exc_info:
        router_delete_centre_activity_preference_by_id(
            centre_activity_preference_id=1,
            db=get_db_session_mock,
            current_user=mock_doctor_jwt,
            token="test-token"
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to delete this Centre Activity Preference"

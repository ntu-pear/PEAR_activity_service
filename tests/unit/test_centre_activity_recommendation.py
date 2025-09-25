import pytest
from unittest.mock import MagicMock, patch
import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import ValidationError
from app.models.centre_activity_recommendation_model import CentreActivityRecommendation as CentreActivityRecommendationModel
from app.schemas.centre_activity_recommendation_schema import CentreActivityRecommendationCreate, CentreActivityRecommendationUpdate, CentreActivityRecommendationResponse
from app.crud.centre_activity_recommendation_crud import (
    create_centre_activity_recommendation,
    get_centre_activity_recommendation_by_id,
    get_centre_activity_recommendations_by_patient_id,
    get_all_centre_activity_recommendations,
    update_centre_activity_recommendation,
    delete_centre_activity_recommendation,
)
# For role tests
from app.routers.centre_activity_recommendation_router import (
    create_centre_activity_recommendation as router_create_centre_activity_recommendation,
    get_all_centre_activity_recommendations as router_get_all_centre_activity_recommendations,
    get_centre_activity_recommendation_by_id as router_get_centre_activity_recommendation_by_id,
    get_centre_activity_recommendations_by_patient_id as router_get_centre_activity_recommendations_by_patient_id,
    update_centre_activity_recommendation as router_update_centre_activity_recommendation,
    delete_centre_activity_recommendation as router_delete_centre_activity_recommendation,
)


@pytest.fixture
def create_centre_activity_recommendation_schema(base_centre_activity_recommendation_data):
    return CentreActivityRecommendationCreate(**base_centre_activity_recommendation_data)

@pytest.fixture
def update_centre_activity_recommendation_schema(base_centre_activity_recommendation_data_list):
    return CentreActivityRecommendationUpdate(**base_centre_activity_recommendation_data_list[1])


# ===== CREATE tests ======
@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_by_id")
def test_create_centre_activity_recommendation_success(mock_get_centre_activity, mock_get_patient, mock_get_patient_allocation,
                                                  get_db_session_mock, mock_doctor_user, 
                                                  create_centre_activity_recommendation_schema,
                                                 existing_activity, mock_patient_service_response, mock_doctor_allocation_response):
    """Creates Centre Activity Recommendation when all conditions are met"""

    # Mock no existing recommendation
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None

    # Mock centre activity exists
    mock_get_centre_activity.return_value = existing_activity
    
    # Mock patient exists and doctor has access
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_doctor_allocation_response
    
    result = create_centre_activity_recommendation(
        db=get_db_session_mock,
        centre_activity_recommendation_data=create_centre_activity_recommendation_schema,
        current_user_info=mock_doctor_user,
    )

    assert result.centre_activity_id == create_centre_activity_recommendation_schema.centre_activity_id
    assert result.patient_id == create_centre_activity_recommendation_schema.patient_id
    assert result.doctor_id == create_centre_activity_recommendation_schema.doctor_id
    assert result.doctor_recommendation == create_centre_activity_recommendation_schema.doctor_recommendation
    assert result.doctor_remarks == create_centre_activity_recommendation_schema.doctor_remarks
    assert result.created_by_id == mock_doctor_user["id"]
    
    get_db_session_mock.add.assert_called()  # Called twice: once for recommendation, once for outbox_event
    assert get_db_session_mock.add.call_count == 2
    get_db_session_mock.commit.assert_called_once()

@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_by_id")
def test_create_centre_activity_recommendation_duplicate_fail(mock_get_centre_activity, mock_get_patient,
                                                        mock_get_patient_allocation, get_db_session_mock,
                                                        mock_doctor_user, create_centre_activity_recommendation_schema,
                                                        existing_activity, existing_centre_activity_recommendation,
                                                        mock_patient_service_response, mock_doctor_allocation_response):
    """Raises HTTPException when duplicate Centre Activity Recommendation exists"""

    # Mock existing recommendation found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity_recommendation

    # Mock centre activity exists
    mock_get_centre_activity.return_value = existing_activity
    
    # Mock patient exists and doctor has access
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_doctor_allocation_response

    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_recommendation(
            db=get_db_session_mock,
            centre_activity_recommendation_data=create_centre_activity_recommendation_schema,
            current_user_info=mock_doctor_user,
        )

    assert exc_info.value.status_code == 400
    assert "Centre Activity Recommendation with these attributes already exists" in exc_info.value.detail["message"]

@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_by_id")
def test_create_centre_activity_recommendation_patient_not_found(mock_get_centre_activity, mock_get_patient, mock_get_patient_allocation,
                                                          get_db_session_mock, mock_doctor_user,
                                                          create_centre_activity_recommendation_schema, existing_activity):
    """Raises HTTPException when patient not found"""

    # Mock no existing recommendation (so duplicate check passes)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    get_db_session_mock.query.return_value = mock_query
    
    # Mock centre activity exists
    mock_get_centre_activity.return_value = existing_activity

    # Mock patient not found
    mock_patient_response = MagicMock()
    mock_patient_response.status_code = 404
    mock_get_patient.return_value = mock_patient_response

    mock_get_patient_allocation.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_recommendation(
            db=get_db_session_mock,
            centre_activity_recommendation_data=create_centre_activity_recommendation_schema,
            current_user_info=mock_doctor_user,
        )

    assert exc_info.value.status_code == 404
    assert "Patient not found or not accessible" in exc_info.value.detail

@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_by_id")
def test_create_centre_activity_recommendation_doctor_not_allocated(mock_get_centre_activity, mock_get_patient, mock_get_patient_allocation,
                                                             get_db_session_mock, mock_doctor_user,
                                                             create_centre_activity_recommendation_schema,
                                                             existing_activity, mock_patient_service_response):
    """Raises HTTPException when doctor is not allocated to patient"""

    # Mock no existing recommendation (so duplicate check passes)
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    get_db_session_mock.query.return_value = mock_query
    
    # Mock centre activity exists
    mock_get_centre_activity.return_value = existing_activity

    # Mock patient exists
    mock_get_patient.return_value = mock_patient_service_response
    
    # Mock doctor not allocated to patient
    mock_allocation_response = MagicMock()
    mock_allocation_response.status_code = 200
    mock_allocation_response.json.return_value = {
        "patientId": 1,
        "caregiverId": "3",
        "supervisorId": "2",
        "doctorId": "999"  # Different doctor ID
    }
    mock_get_patient_allocation.return_value = mock_allocation_response

    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_recommendation(
            db=get_db_session_mock,
            centre_activity_recommendation_data=create_centre_activity_recommendation_schema,
            current_user_info=mock_doctor_user,
        )

    assert exc_info.value.status_code == 403
    assert "You do not have permission to create a Centre Activity Recommendation for this Patient" in exc_info.value.detail


# ===== GET by ID tests ======
def test_get_centre_activity_recommendation_by_id_success(get_db_session_mock, existing_centre_activity_recommendation):
    """Successfully retrieves Centre Activity Recommendation by ID"""
    
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = existing_centre_activity_recommendation

    result = get_centre_activity_recommendation_by_id(
        db=get_db_session_mock,
        centre_activity_recommendation_id=1
    )

    assert result == existing_centre_activity_recommendation
    assert result.id == 1

def test_get_centre_activity_recommendation_by_id_not_found(get_db_session_mock):
    """Raises HTTPException when Centre Activity Recommendation not found"""
    
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_centre_activity_recommendation_by_id(
            db=get_db_session_mock,
            centre_activity_recommendation_id=999
        )

    assert exc_info.value.status_code == 404
    assert "Centre Activity Recommendation not found" in exc_info.value.detail

def test_get_centre_activity_recommendation_by_id_include_deleted(get_db_session_mock, soft_deleted_centre_activity_recommendation):
    """Successfully retrieves soft-deleted Centre Activity Recommendation when include_deleted=True"""
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = soft_deleted_centre_activity_recommendation

    result = get_centre_activity_recommendation_by_id(
        db=get_db_session_mock,
        centre_activity_recommendation_id=1,
        include_deleted=True
    )

    assert result == soft_deleted_centre_activity_recommendation
    assert result.is_deleted == True


# ===== GET ALL tests ======
def test_get_all_centre_activity_recommendations_success(get_db_session_mock, mock_doctor_user, existing_centre_activity_recommendations):
    """Successfully retrieves all Centre Activity Recommendations"""
    
    get_db_session_mock.query.return_value.filter.return_value.all.return_value = existing_centre_activity_recommendations

    result = get_all_centre_activity_recommendations(
        db=get_db_session_mock,
        current_user_info=mock_doctor_user
    )

    assert len(result) == 2
    assert result == existing_centre_activity_recommendations

def test_get_all_centre_activity_recommendations_not_found(get_db_session_mock, mock_doctor_user):
    """Raises HTTPException when no Centre Activity Recommendations found"""
    
    get_db_session_mock.query.return_value.filter.return_value.all.return_value = []

    with pytest.raises(HTTPException) as exc_info:
        get_all_centre_activity_recommendations(
            db=get_db_session_mock,
            current_user_info=mock_doctor_user
        )

    assert exc_info.value.status_code == 404
    assert "No Centre Activity Recommendations found" in exc_info.value.detail


# ===== GET by Patient ID tests ======
@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
def test_get_centre_activity_recommendations_by_patient_id_success(mock_get_patient, mock_get_patient_allocation,
                                                            get_db_session_mock, mock_doctor_user,
                                                            existing_centre_activity_recommendations,
                                                            mock_patient_service_response, mock_doctor_allocation_response):
    """Successfully retrieves Centre Activity Recommendations by patient ID"""
    
    # Mock patient exists and doctor has access
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_doctor_allocation_response
    
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.all.return_value = existing_centre_activity_recommendations

    result = get_centre_activity_recommendations_by_patient_id(
        db=get_db_session_mock,
        patient_id=1,
        current_user_info=mock_doctor_user
    )

    assert len(result) == 2
    assert result == existing_centre_activity_recommendations

@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
def test_get_centre_activity_recommendations_by_patient_id_not_found(mock_get_patient, mock_get_patient_allocation,
                                                               get_db_session_mock, mock_doctor_user,
                                                               mock_patient_service_response, mock_doctor_allocation_response):
    """Raises HTTPException when no Centre Activity Recommendations found for patient"""
    
    # Mock patient exists and doctor has access
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_doctor_allocation_response
    
    get_db_session_mock.query.return_value.filter.return_value.filter.return_value.all.return_value = []

    with pytest.raises(HTTPException) as exc_info:
        get_centre_activity_recommendations_by_patient_id(
            db=get_db_session_mock,
            patient_id=1,
            current_user_info=mock_doctor_user
        )

    assert exc_info.value.status_code == 404
    assert "No Centre Activity Recommendations found for Patient ID 1" in exc_info.value.detail


# ===== UPDATE tests ======
@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_by_id")
@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_recommendation_by_id")
def test_update_centre_activity_recommendation_success(mock_get_recommendation, mock_get_centre_activity, mock_get_patient, 
                                                mock_get_patient_allocation, get_db_session_mock, mock_doctor_user,
                                                update_centre_activity_recommendation_schema, existing_centre_activity_recommendation,
                                                existing_activity, mock_patient_service_response, mock_doctor_allocation_response):
    """Successfully updates Centre Activity Recommendation"""
    
    # Mock existing recommendation found
    mock_get_recommendation.return_value = existing_centre_activity_recommendation
    
    # Mock no duplicate found (excluding current ID) - need to properly chain the filters
    mock_query = MagicMock()
    mock_filter_chain = MagicMock()
    mock_filter_chain.filter.return_value.first.return_value = None
    mock_query.filter.return_value = mock_filter_chain
    get_db_session_mock.query.return_value = mock_query
    
    # Mock dependencies exist
    mock_get_centre_activity.return_value = existing_activity
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_doctor_allocation_response

    result = update_centre_activity_recommendation(
        db=get_db_session_mock,
        centre_activity_recommendation_data=update_centre_activity_recommendation_schema,
        current_user_info=mock_doctor_user,
    )

    assert result == existing_centre_activity_recommendation
    get_db_session_mock.commit.assert_called_once()

@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_recommendation_by_id")
def test_update_centre_activity_recommendation_not_found(mock_get_recommendation, get_db_session_mock, mock_doctor_user,
                                                   update_centre_activity_recommendation_schema):
    """Raises HTTPException when Centre Activity Recommendation to update not found"""
    
    # Mock recommendation not found
    mock_get_recommendation.side_effect = HTTPException(status_code=404, detail="Centre Activity Recommendation not found")

    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_recommendation(
            db=get_db_session_mock,
            centre_activity_recommendation_data=update_centre_activity_recommendation_schema,
            current_user_info=mock_doctor_user,
        )

    assert exc_info.value.status_code == 404


# ===== DELETE tests ======
@patch("app.services.patient_service.get_patient_allocation_by_patient_id")
@patch("app.services.patient_service.get_patient_by_id")
@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_recommendation_by_id")
def test_delete_centre_activity_recommendation_success(mock_get_recommendation, mock_get_patient, mock_get_patient_allocation,
                                                get_db_session_mock, mock_doctor_user, existing_centre_activity_recommendation,
                                                mock_patient_service_response, mock_doctor_allocation_response):
    """Successfully soft deletes Centre Activity Recommendation"""
    
    # Mock existing recommendation found
    mock_get_recommendation.return_value = existing_centre_activity_recommendation
    
    # Mock patient exists and doctor has access
    mock_get_patient.return_value = mock_patient_service_response
    mock_get_patient_allocation.return_value = mock_doctor_allocation_response

    result = delete_centre_activity_recommendation(
        db=get_db_session_mock,
        centre_activity_recommendation_id=1,
        current_user_info=mock_doctor_user,
    )

    assert result == existing_centre_activity_recommendation
    assert result.is_deleted == True
    get_db_session_mock.commit.assert_called_once()

@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_recommendation_by_id")
def test_delete_centre_activity_recommendation_not_found(mock_get_recommendation, get_db_session_mock, mock_doctor_user):
    """Raises HTTPException when Centre Activity Recommendation to delete not found"""
    
    # Mock recommendation not found
    mock_get_recommendation.side_effect = HTTPException(status_code=404, detail="Centre Activity Recommendation not found")

    with pytest.raises(HTTPException) as exc_info:
        delete_centre_activity_recommendation(
            db=get_db_session_mock,
            centre_activity_recommendation_id=999,
            current_user_info=mock_doctor_user,
        )

    assert exc_info.value.status_code == 404


# === Role-based Access Control Tests ===
@patch("app.crud.centre_activity_recommendation_crud.create_centre_activity_recommendation")
def test_create_centre_activity_recommendation_role_access_success(mock_crud_create, get_db_session_mock, 
                                                             mock_doctor_jwt, 
                                                             create_centre_activity_recommendation_schema):
    """Tests that Doctor can create Centre Activity Recommendation"""
    
    mock_result = MagicMock()
    mock_result.centre_activity_id = create_centre_activity_recommendation_schema.centre_activity_id
    mock_result.patient_id = create_centre_activity_recommendation_schema.patient_id
    mock_result.doctor_id = create_centre_activity_recommendation_schema.doctor_id
    mock_result.doctor_recommendation = create_centre_activity_recommendation_schema.doctor_recommendation
    mock_crud_create.return_value = mock_result

    result = router_create_centre_activity_recommendation(
        payload=create_centre_activity_recommendation_schema,
        db=get_db_session_mock,
        user_and_token=(mock_doctor_jwt, "test-token")
    )

    assert result.centre_activity_id == create_centre_activity_recommendation_schema.centre_activity_id
    assert result.patient_id == create_centre_activity_recommendation_schema.patient_id
    assert result.doctor_recommendation == create_centre_activity_recommendation_schema.doctor_recommendation

@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_caregiver_jwt", "mock_admin_jwt"])
def test_create_centre_activity_recommendation_role_access_fail(get_db_session_mock, mock_user_fixtures, request, create_centre_activity_recommendation_schema):
    """Fails when non-doctor tries to create Centre Activity Recommendation"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_create_centre_activity_recommendation(
            payload=create_centre_activity_recommendation_schema,
            db=get_db_session_mock,
            user_and_token=(mock_user_roles, "test-token")
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == f"You do not have permission to create a Centre Activity Recommendation {mock_user_roles.roleName}"

@patch("app.crud.centre_activity_recommendation_crud.get_all_centre_activity_recommendations")
def test_get_all_centre_activity_recommendations_role_access_success(mock_crud_get, get_db_session_mock, 
                                                           existing_centre_activity_recommendations,
                                                           mock_doctor_jwt):
    """Tests that Doctor can get all Centre Activity Recommendations"""
    
    mock_crud_get.return_value = existing_centre_activity_recommendations

    result = router_get_all_centre_activity_recommendations(
        include_deleted=False,
        db=get_db_session_mock,
        user_and_token=(mock_doctor_jwt, "test-token")
    )

    assert len(result) == 2
    assert result == existing_centre_activity_recommendations

@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_admin_jwt"])
def test_get_all_centre_activity_recommendations_role_access_fail(get_db_session_mock, mock_user_fixtures, request):
    """Fails when non-doctor tries to get all Centre Activity Recommendations"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_get_all_centre_activity_recommendations(
            include_deleted=False,
            db=get_db_session_mock,
            user_and_token=(mock_user_roles, "test-token")
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to access Centre Activity Recommendations"

@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_recommendation_by_id")
def test_get_centre_activity_recommendation_by_id_role_access_success(mock_crud_get, get_db_session_mock,
                                                                existing_centre_activity_recommendation,
                                                                mock_doctor_jwt):
    """Tests that Doctor can get Centre Activity Recommendation by ID"""
    
    mock_crud_get.return_value = existing_centre_activity_recommendation

    result = router_get_centre_activity_recommendation_by_id(
        centre_activity_recommendation_id=1,
        include_deleted=False,
        db=get_db_session_mock,
        user_and_token=(mock_doctor_jwt, "test-token")
    )

    assert result == existing_centre_activity_recommendation

@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_admin_jwt"])
def test_get_centre_activity_recommendation_by_id_role_access_fail(get_db_session_mock, mock_user_fixtures, request):
    """Fails when non-doctor tries to get Centre Activity Recommendation by ID"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_get_centre_activity_recommendation_by_id(
            centre_activity_recommendation_id=1,
            include_deleted=False,
            db=get_db_session_mock,
            user_and_token=(mock_user_roles, "test-token")
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to access Centre Activity Recommendations"

@patch("app.crud.centre_activity_recommendation_crud.get_centre_activity_recommendations_by_patient_id")
def test_get_centre_activity_recommendations_by_patient_id_role_access_success(mock_crud_get, get_db_session_mock,
                                                                         existing_centre_activity_recommendations,
                                                                         mock_doctor_jwt):
    """Tests that Doctor can get Centre Activity Recommendations by patient ID"""
    
    mock_crud_get.return_value = existing_centre_activity_recommendations

    result = router_get_centre_activity_recommendations_by_patient_id(
        patient_id=1,
        include_deleted=False,
        db=get_db_session_mock,
        user_and_token=(mock_doctor_jwt, "test-token")
    )

    assert len(result) == 2
    assert result == existing_centre_activity_recommendations

@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_admin_jwt"])
def test_get_centre_activity_recommendations_by_patient_id_role_access_fail(get_db_session_mock, mock_user_fixtures, request):
    """Fails when non-doctor tries to get Centre Activity Recommendations by patient ID"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_get_centre_activity_recommendations_by_patient_id(
            patient_id=1,
            include_deleted=False,
            db=get_db_session_mock,
            user_and_token=(mock_user_roles, "test-token")
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to access Centre Activity Recommendations"

@patch("app.crud.centre_activity_recommendation_crud.update_centre_activity_recommendation")
def test_update_centre_activity_recommendation_role_access_success(mock_crud_update, get_db_session_mock,
                                                            existing_centre_activity_recommendation,
                                                            mock_doctor_jwt,
                                                            update_centre_activity_recommendation_schema):
    """Tests that Doctor can update Centre Activity Recommendation"""
    
    mock_crud_update.return_value = existing_centre_activity_recommendation

    result = router_update_centre_activity_recommendation(
        centre_activity_recommendation_id=1,
        payload=update_centre_activity_recommendation_schema,
        db=get_db_session_mock,
        user_and_token=(mock_doctor_jwt, "test-token")
    )

    assert result == existing_centre_activity_recommendation
    # Verify that the payload ID was set correctly
    assert update_centre_activity_recommendation_schema.centre_activity_recommendation_id == 1

@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_caregiver_jwt", "mock_admin_jwt"])
def test_update_centre_activity_recommendation_role_access_fail(get_db_session_mock, mock_user_fixtures, request, update_centre_activity_recommendation_schema):
    """Fails when non-doctor tries to update Centre Activity Recommendation"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_update_centre_activity_recommendation(
            centre_activity_recommendation_id=1,
            payload=update_centre_activity_recommendation_schema,
            db=get_db_session_mock,
            user_and_token=(mock_user_roles, "test-token")
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to update Centre Activity Recommendations"

@patch("app.crud.centre_activity_recommendation_crud.delete_centre_activity_recommendation")
def test_delete_centre_activity_recommendation_role_access_success(mock_crud_delete, get_db_session_mock,
                                                            existing_centre_activity_recommendation,
                                                            mock_doctor_jwt):
    """Tests that Doctor can delete Centre Activity Recommendation"""
    
    mock_crud_delete.return_value = existing_centre_activity_recommendation

    result = router_delete_centre_activity_recommendation(
        centre_activity_recommendation_id=1,
        db=get_db_session_mock,
        user_and_token=(mock_doctor_jwt, "test-token")
    )

    assert result == existing_centre_activity_recommendation

@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt", "mock_caregiver_jwt", "mock_admin_jwt"])
def test_delete_centre_activity_recommendation_role_access_fail(get_db_session_mock, mock_user_fixtures, request):
    """Fails when non-doctor tries to delete Centre Activity Recommendation"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_delete_centre_activity_recommendation(
            centre_activity_recommendation_id=1,
            db=get_db_session_mock,
            user_and_token=(mock_user_roles, "test-token")
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "You do not have permission to delete Centre Activity Recommendations"


# ===== Schema validation tests ======
def test_centre_activity_recommendation_create_schema_validation():
    """Test CentreActivityRecommendationCreate schema validation"""
    valid_data = {
        "centre_activity_id": 1,
        "patient_id": 1,
        "doctor_id": 456,
        "doctor_recommendation": 1,
        "doctor_remarks": "Recommended for cognitive improvement",
        "created_by_id": "456"
    }
    
    schema = CentreActivityRecommendationCreate(**valid_data)
    assert schema.centre_activity_id == 1
    assert schema.patient_id == 1
    assert schema.doctor_id == 456
    assert schema.doctor_recommendation == 1
    assert schema.doctor_remarks == "Recommended for cognitive improvement"
    assert schema.created_by_id == "456"

def test_centre_activity_recommendation_create_schema_validation_missing_field():
    """Test CentreActivityRecommendationCreate schema validation with missing required field"""
    invalid_data = {
        "centre_activity_id": 1,
        "patient_id": 1,
        # Missing doctor_id
        "doctor_recommendation": 1,
        "doctor_remarks": "Recommended for cognitive improvement",
        "created_by_id": "456"
    }
    
    with pytest.raises(ValidationError):
        CentreActivityRecommendationCreate(**invalid_data)

def test_centre_activity_recommendation_update_schema_validation():
    """Test CentreActivityRecommendationUpdate schema validation"""
    valid_data = {
        "id": 1,  # This gets aliased to centre_activity_recommendation_id
        "centre_activity_id": 2,
        "patient_id": 1,
        "doctor_id": 456,
        "doctor_recommendation": -1,
        "doctor_remarks": "Updated remarks",
        "is_deleted": False,
        "modified_by_id": "456",
        "modified_date": datetime.datetime.now()
    }
    
    schema = CentreActivityRecommendationUpdate(**valid_data)
    assert schema.centre_activity_recommendation_id == 1
    assert schema.centre_activity_id == 2
    assert schema.doctor_remarks == "Updated remarks"

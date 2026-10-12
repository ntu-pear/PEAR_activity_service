import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.routers.aggregated_router import (
    get_activity_preference_table_data,
    get_activity_exclusion_table_data,
)
from app.schemas.aggregated_schema import ActivityPreferenceTableData, ActivityExclusionTableData
from app.schemas.activity_schema import ActivityRead
from app.schemas.centre_activity_schema import CentreActivityResponse
from app.schemas.centre_activity_preference_schema import CentreActivityPreferenceResponse
from app.schemas.centre_activity_recommendation_schema import CentreActivityRecommendationResponse
from app.schemas.centre_activity_exclusion_schema import CentreActivityExclusionResponse
from app.schemas.ref_patient import RefPatient


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def sample_activity():
    return ActivityRead(
        id=1,
        title="Test Activity",
        description="Test description",
        is_deleted=False,
        created_date=datetime.now(),
        modified_date=datetime.now(),
        created_by_id="user1",
        modified_by_id=None,
    )


@pytest.fixture
def sample_centre_activity():
    return CentreActivityResponse(
        id=1,
        activity_id=1,
        is_compulsory=False,
        is_fixed=True,
        is_group=False,
        start_date=date.today(),
        end_date=date(2999, 12, 31),
        min_duration=60,
        max_duration=60,
        min_people_req=1,
        fixed_time_slots=None,
        is_deleted=False,
        created_date=datetime.now(),
        modified_date=None,
        created_by_id="user1",
        modified_by_id=None,
    )


@pytest.fixture
def sample_preference():
    return CentreActivityPreferenceResponse(
        id=1,
        centre_activity_id=1,
        patient_id=1,
        is_like=1,
        is_deleted=False,
        created_date=datetime.now(),
        modified_date=None,
        created_by_id="user1",
        modified_by_id=None,
    )


@pytest.fixture
def sample_recommendation():
    return CentreActivityRecommendationResponse(
        id=1,
        centre_activity_id=1,
        patient_id=1,
        doctor_recommendation=1,
        doctor_remarks=None,
        is_deleted=False,
        doctor_id="doc1",
        created_date=datetime.now(),
        modified_date=None,
        created_by_id="user1",
        modified_by_id=None,
    )


@pytest.fixture
def sample_exclusion():
    return CentreActivityExclusionResponse(
        id=1,
        centre_activity_id=1,
        patient_id=1,
        exclusion_remarks=None,
        start_date=date.today(),
        end_date=None,
        is_deleted=False,
        created_date=datetime.now(),
        modified_date=datetime.now(),
        created_by_id="user1",
        modified_by_id=None,
    )


@pytest.fixture
def sample_patient():
    return RefPatient(
        id=1,
        name="Test Patient",
        preferred_name=None,
        update_bit="1",
        start_date=datetime.now(),
        end_date=None,
        is_active="1",
        is_deleted="0",
        created_date=datetime.now(),
        modified_date=datetime.now(),
        created_by_id="user1",
        modified_by_id="user1",
    )


# ===== activity-preference-table =====

@patch("app.crud.ref_patient_crud.get_ref_patients")
@patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusions")
@patch("app.crud.centre_activity_recommendation_crud.get_all_centre_activity_recommendations")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_preferences")
@patch("app.crud.centre_activity_crud.get_centre_activities")
@patch("app.crud.activity_crud.get_activities")
def test_get_activity_preference_table_returns_all_fields(
    mock_get_activities,
    mock_get_centre_activities,
    mock_get_preferences,
    mock_get_recommendations,
    mock_get_exclusions,
    mock_get_patients,
    mock_db,
    mock_supervisor_jwt,
    sample_activity,
    sample_centre_activity,
    sample_preference,
    sample_recommendation,
    sample_exclusion,
    sample_patient,
):
    mock_get_activities.return_value = [sample_activity]
    mock_get_centre_activities.return_value = [sample_centre_activity]
    mock_get_preferences.return_value = [sample_preference]
    mock_get_recommendations.return_value = [sample_recommendation]
    mock_get_exclusions.return_value = [sample_exclusion]
    mock_get_patients.return_value = ([sample_patient], 1, 1)

    result = get_activity_preference_table_data(
        db=mock_db,
        current_user=mock_supervisor_jwt,
        include_deleted=False,
    )

    assert isinstance(result, ActivityPreferenceTableData)
    assert len(result.activities) == 1
    assert len(result.centre_activities) == 1
    assert len(result.preferences) == 1
    assert len(result.recommendations) == 1
    assert len(result.exclusions) == 1
    assert len(result.patients) == 1


@patch("app.crud.ref_patient_crud.get_ref_patients")
@patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusions")
@patch("app.crud.centre_activity_recommendation_crud.get_all_centre_activity_recommendations")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_preferences")
@patch("app.crud.centre_activity_crud.get_centre_activities")
@patch("app.crud.activity_crud.get_activities")
def test_get_activity_preference_table_empty_data(
    mock_get_activities,
    mock_get_centre_activities,
    mock_get_preferences,
    mock_get_recommendations,
    mock_get_exclusions,
    mock_get_patients,
    mock_db,
    mock_supervisor_jwt,
):
    mock_get_activities.return_value = []
    mock_get_centre_activities.return_value = []
    mock_get_preferences.return_value = []
    mock_get_recommendations.return_value = []
    mock_get_exclusions.return_value = []
    mock_get_patients.return_value = ([], 0, 0)

    result = get_activity_preference_table_data(
        db=mock_db,
        current_user=mock_supervisor_jwt,
        include_deleted=False,
    )

    assert isinstance(result, ActivityPreferenceTableData)
    assert result.activities == []
    assert result.preferences == []
    assert result.recommendations == []
    assert result.exclusions == []
    assert result.patients == []


@patch("app.crud.ref_patient_crud.get_ref_patients")
@patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusions")
@patch("app.crud.centre_activity_recommendation_crud.get_all_centre_activity_recommendations")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_preferences")
@patch("app.crud.centre_activity_crud.get_centre_activities")
@patch("app.crud.activity_crud.get_activities")
def test_get_activity_preference_table_no_auth(
    mock_get_activities,
    mock_get_centre_activities,
    mock_get_preferences,
    mock_get_recommendations,
    mock_get_exclusions,
    mock_get_patients,
    mock_db,
):
    mock_get_activities.return_value = []
    mock_get_centre_activities.return_value = []
    mock_get_preferences.return_value = []
    mock_get_recommendations.return_value = []
    mock_get_exclusions.return_value = []
    mock_get_patients.return_value = ([], 0, 0)

    result = get_activity_preference_table_data(
        db=mock_db,
        current_user=None,
        include_deleted=False,
    )

    assert isinstance(result, ActivityPreferenceTableData)


# ===== activity-exclusion-table =====

@patch("app.crud.ref_patient_crud.get_ref_patients")
@patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusions")
@patch("app.crud.centre_activity_crud.get_centre_activities")
@patch("app.crud.activity_crud.get_activities")
def test_get_activity_exclusion_table_returns_all_fields(
    mock_get_activities,
    mock_get_centre_activities,
    mock_get_exclusions,
    mock_get_patients,
    mock_db,
    mock_supervisor_jwt,
    sample_activity,
    sample_centre_activity,
    sample_exclusion,
    sample_patient,
):
    mock_get_activities.return_value = [sample_activity]
    mock_get_centre_activities.return_value = [sample_centre_activity]
    mock_get_exclusions.return_value = [sample_exclusion]
    mock_get_patients.return_value = ([sample_patient], 1, 1)

    result = get_activity_exclusion_table_data(
        db=mock_db,
        current_user=mock_supervisor_jwt,
        include_deleted=False,
    )

    assert isinstance(result, ActivityExclusionTableData)
    assert len(result.activities) == 1
    assert len(result.centre_activities) == 1
    assert len(result.exclusions) == 1
    assert len(result.patients) == 1


@patch("app.crud.ref_patient_crud.get_ref_patients")
@patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusions")
@patch("app.crud.centre_activity_crud.get_centre_activities")
@patch("app.crud.activity_crud.get_activities")
def test_get_activity_exclusion_table_empty_data(
    mock_get_activities,
    mock_get_centre_activities,
    mock_get_exclusions,
    mock_get_patients,
    mock_db,
    mock_supervisor_jwt,
):
    mock_get_activities.return_value = []
    mock_get_centre_activities.return_value = []
    mock_get_exclusions.return_value = []
    mock_get_patients.return_value = ([], 0, 0)

    result = get_activity_exclusion_table_data(
        db=mock_db,
        current_user=mock_supervisor_jwt,
        include_deleted=False,
    )

    assert isinstance(result, ActivityExclusionTableData)
    assert result.activities == []
    assert result.exclusions == []
    assert result.patients == []


@patch("app.crud.ref_patient_crud.get_ref_patients")
@patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusions")
@patch("app.crud.centre_activity_crud.get_centre_activities")
@patch("app.crud.activity_crud.get_activities")
def test_get_activity_exclusion_table_no_auth(
    mock_get_activities,
    mock_get_centre_activities,
    mock_get_exclusions,
    mock_get_patients,
    mock_db,
):
    mock_get_activities.return_value = []
    mock_get_centre_activities.return_value = []
    mock_get_exclusions.return_value = []
    mock_get_patients.return_value = ([], 0, 0)

    result = get_activity_exclusion_table_data(
        db=mock_db,
        current_user=None,
        include_deleted=False,
    )

    assert isinstance(result, ActivityExclusionTableData)


# ===== activity-preference-table/patient/{patient_id} =====

@patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusions_by_patient_id")
@patch("app.crud.centre_activity_recommendation_crud.get_all_centre_activity_recommendations")
@patch("app.crud.centre_activity_preference_crud.get_centre_activity_preferences_by_patient_id")
@patch("app.crud.centre_activity_crud.get_centre_activities")
@patch("app.crud.activity_crud.get_activities")
@patch("app.crud.ref_patient_crud.get_ref_patient_by_id")
def test_get_activity_preference_table_by_patient_returns_data(
    mock_get_patient,
    mock_get_activities,
    mock_get_centre_activities,
    mock_get_preferences,
    mock_get_recommendations,
    mock_get_exclusions,
    mock_db,
    mock_supervisor_jwt,
    sample_activity,
    sample_centre_activity,
    sample_preference,
    sample_recommendation,
    sample_exclusion,
    sample_patient,
):
    mock_get_patient.return_value = sample_patient
    mock_get_activities.return_value = [sample_activity]
    mock_get_centre_activities.return_value = [sample_centre_activity]
    mock_get_preferences.return_value = [sample_preference]
    mock_get_recommendations.return_value = [sample_recommendation]
    mock_get_exclusions.return_value = [sample_exclusion]

    from app.routers.aggregated_router import get_activity_preference_table_data_by_patient
    result = get_activity_preference_table_data_by_patient(
        patient_id=1,
        db=mock_db,
        current_user=mock_supervisor_jwt,
        include_deleted=False,
    )

    assert isinstance(result, ActivityPreferenceTableData)
    assert len(result.patients) == 1
    assert len(result.preferences) == 1
    assert len(result.exclusions) == 1


@patch("app.crud.ref_patient_crud.get_ref_patient_by_id")
def test_get_activity_preference_table_by_patient_not_found(mock_get_patient, mock_db, mock_supervisor_jwt):
    from fastapi import HTTPException
    mock_get_patient.return_value = None

    from app.routers.aggregated_router import get_activity_preference_table_data_by_patient
    with pytest.raises(HTTPException) as exc_info:
        get_activity_preference_table_data_by_patient(
            patient_id=999,
            db=mock_db,
            current_user=mock_supervisor_jwt,
            include_deleted=False,
        )
    assert exc_info.value.status_code == 404


# ===== activity-exclusion-table/patient/{patient_id} =====

@patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusions_by_patient_id")
@patch("app.crud.centre_activity_crud.get_centre_activities")
@patch("app.crud.activity_crud.get_activities")
@patch("app.crud.ref_patient_crud.get_ref_patient_by_id")
def test_get_activity_exclusion_table_by_patient_returns_data(
    mock_get_patient,
    mock_get_activities,
    mock_get_centre_activities,
    mock_get_exclusions,
    mock_db,
    mock_supervisor_jwt,
    sample_activity,
    sample_centre_activity,
    sample_exclusion,
    sample_patient,
):
    mock_get_patient.return_value = sample_patient
    mock_get_activities.return_value = [sample_activity]
    mock_get_centre_activities.return_value = [sample_centre_activity]
    mock_get_exclusions.return_value = [sample_exclusion]

    from app.routers.aggregated_router import get_activity_exclusion_table_data_by_patient
    result = get_activity_exclusion_table_data_by_patient(
        patient_id=1,
        db=mock_db,
        current_user=mock_supervisor_jwt,
        include_deleted=False,
    )

    assert isinstance(result, ActivityExclusionTableData)
    assert len(result.patients) == 1
    assert len(result.exclusions) == 1


@patch("app.crud.ref_patient_crud.get_ref_patient_by_id")
def test_get_activity_exclusion_table_by_patient_not_found(mock_get_patient, mock_db, mock_supervisor_jwt):
    from fastapi import HTTPException
    mock_get_patient.return_value = None

    from app.routers.aggregated_router import get_activity_exclusion_table_data_by_patient
    with pytest.raises(HTTPException) as exc_info:
        get_activity_exclusion_table_data_by_patient(
            patient_id=999,
            db=mock_db,
            current_user=mock_supervisor_jwt,
            include_deleted=False,
        )
    assert exc_info.value.status_code == 404

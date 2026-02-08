import pytest
from unittest.mock import MagicMock, patch
from datetime import date, time, timedelta
from fastapi import HTTPException, status
from pydantic import ValidationError
from app.schemas.routine_schema import RoutineCreate, RoutineUpdate
from app.crud.routine_crud import (
    create_routine,
    get_routine_by_id,
    get_routines,
    get_routines_by_patient_id,
    update_routine,
    delete_routine,
    _check_for_duplicate_routine,
    _validate_routine_data,
)
from app.routers.routine_router import (
    create_routine as router_create_routine,
    list_routines as router_list_routines,
    get_routine_by_id as router_get_routine_by_id,
    update_routine as router_update_routine,
    delete_routine as router_delete_routine,
)


# Stub out real logging so we don't try to JSON‑serialize MagicMocks
@pytest.fixture(autouse=True)
def disable_crud_logging(monkeypatch):
    """Auto-disable CRUD logging to prevent JSON serialization issues with MagicMocks"""
    from app.crud import routine_crud
    monkeypatch.setattr(routine_crud, "log_crud_action", lambda *args, **kwargs: None)


@pytest.fixture
def create_routine_schema(base_routine_data):
    """RoutineCreate schema instance"""
    return RoutineCreate(**base_routine_data)


@pytest.fixture
def update_routine_schema(base_routine_data_list):
    """RoutineUpdate schema instance"""
    return RoutineUpdate(**base_routine_data_list[1])


# ===== Schema Validation Tests =====

@pytest.mark.parametrize(
    "override_fields, expected_error",
    [
        # start_time >= end_time
        ({"start_time": time(10, 0), "end_time": time(9, 0)}, "start_time must be before end_time"),
        ({"start_time": time(10, 0), "end_time": time(10, 0)}, "start_time must be before end_time"),
        
        # start_date >= end_date
        ({"start_date": date.today() + timedelta(days=30), "end_date": date.today() + timedelta(days=1)}, "start_date must be before end_date"),
        ({"start_date": date.today() + timedelta(days=10), "end_date": date.today() + timedelta(days=10)}, "start_date must be before end_date"),
        
        # start_date in the past
        ({"start_date": date.today() - timedelta(days=1)}, "start_date cannot be in the past"),
        
        # day_of_week bitmask validation
        ({"day_of_week": 0}, "Input should be greater than or equal to 1"),
        ({"day_of_week": 128}, "Input should be less than or equal to 127"),
        ({"day_of_week": -1}, "Input should be greater than or equal to 1"),
    ]
)
def test_routine_create_validation_fails(base_routine_data, override_fields, expected_error):
    """Raises ValidationError with invalid data for RoutineCreate"""
    data = {**base_routine_data, **override_fields}
    
    with pytest.raises(ValidationError) as exc:
        RoutineCreate(**data)
    
    assert expected_error in str(exc.value)


def test_routine_create_validation_passes(base_routine_data):
    """Successfully creates RoutineCreate schema with valid data"""
    schema = RoutineCreate(**base_routine_data)
    assert schema.activity_id == base_routine_data["activity_id"]
    assert schema.patient_id == base_routine_data["patient_id"]


@pytest.mark.parametrize(
    "day_of_week_bitmask",
    [
        1,    # Monday only
        3,    # Monday + Tuesday
        7,    # Monday + Tuesday + Wednesday
        31,   # Weekdays (Mon-Fri)
        127,  # All days
    ]
)
def test_routine_create_valid_bitmask_combinations(base_routine_data, day_of_week_bitmask):
    """Validates that various valid bitmask combinations pass"""
    data = {**base_routine_data, "day_of_week": day_of_week_bitmask}
    schema = RoutineCreate(**data)
    assert schema.day_of_week == day_of_week_bitmask


# ===== CREATE tests =====

@patch("app.crud.routine_crud.get_patient_by_id")
@patch("app.crud.routine_crud.get_activity_by_id")
def test_create_routine_success(
    mock_get_activity, mock_get_patient,
    get_db_session_mock, mock_supervisor_user,
    create_routine_schema, existing_activity
):
    """Creates routine when all validations pass"""
    mock_get_activity.return_value = existing_activity
    mock_get_patient.return_value = {"patientId": 1}
    
    # No duplicate found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    result = create_routine(
        db=get_db_session_mock,
        routine_data=create_routine_schema,
        current_user_info=mock_supervisor_user
    )
    
    get_db_session_mock.add.assert_called_once()
    get_db_session_mock.commit.assert_called_once()
    
    for field in create_routine_schema.model_fields:
        assert getattr(result, field) == getattr(create_routine_schema, field), f"Mismatch on field: {field}"


@patch("app.crud.routine_crud.get_activity_by_id")
def test_create_routine_activity_not_found(
    mock_get_activity, get_db_session_mock, mock_supervisor_user, create_routine_schema
):
    """Raises HTTPException when activity not found"""
    mock_get_activity.return_value = None
    
    # No duplicate found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        create_routine(
            db=get_db_session_mock,
            routine_data=create_routine_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 404
    assert "Activity with ID" in exc.value.detail


@patch("app.crud.routine_crud.get_activity_by_id")
def test_create_routine_deleted_activity(
    mock_get_activity, get_db_session_mock, mock_supervisor_user, 
    create_routine_schema, existing_activity
):
    """Raises HTTPException when activity is deleted"""
    existing_activity.is_deleted = True
    mock_get_activity.return_value = existing_activity
    
    # No duplicate found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        create_routine(
            db=get_db_session_mock,
            routine_data=create_routine_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 400
    assert "deleted activity" in exc.value.detail


def test_create_routine_duplicate_detected(
    get_db_session_mock, mock_supervisor_user, create_routine_schema, existing_routine
):
    """Raises HTTPException when duplicate routine exists"""
    # Duplicate found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine
    
    with pytest.raises(HTTPException) as exc:
        create_routine(
            db=get_db_session_mock,
            routine_data=create_routine_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 409
    assert "overlapping" in exc.value.detail


def test_create_routine_overlapping_days_detected(get_db_session_mock, base_routine_data, existing_routine):
    """Raises HTTPException when overlapping days in bitmask are detected"""
    # existing_routine has day_of_week=1 (Monday)
    # new routine has day_of_week=3 (Monday + Tuesday) - should conflict
    data = {**base_routine_data, "day_of_week": 3}
    schema = RoutineCreate(**data)
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine
    
    with pytest.raises(HTTPException) as exc:
        _check_for_duplicate_routine(db=get_db_session_mock, routine_data=schema)
    
    assert exc.value.status_code == 409


def test_create_routine_non_overlapping_days_allowed(get_db_session_mock, base_routine_data):
    """Creates routine when days do not overlap"""
    # existing has day_of_week=1 (Monday)
    # new routine has day_of_week=4 (Wednesday) - should not conflict
    data = {**base_routine_data, "day_of_week": 4}
    schema = RoutineCreate(**data)
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    # Should not raise
    _check_for_duplicate_routine(db=get_db_session_mock, routine_data=schema)


def test_create_routine_overlapping_times_detected(get_db_session_mock, base_routine_data, existing_routine):
    """Raises HTTPException when overlapping time ranges are detected"""
    # existing: 9:00-10:00
    # new: 9:30-10:30 - overlaps
    data = {**base_routine_data, "start_time": time(9, 30), "end_time": time(10, 30)}
    schema = RoutineCreate(**data)
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine
    
    with pytest.raises(HTTPException) as exc:
        _check_for_duplicate_routine(db=get_db_session_mock, routine_data=schema)
    
    assert exc.value.status_code == 409


# ===== GET tests =====

def test_get_routine_by_id_success(get_db_session_mock, existing_routine):
    """Successfully retrieves routine by ID"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine
    
    result = get_routine_by_id(db=get_db_session_mock, routine_id=1)
    
    assert result == existing_routine


def test_get_routine_by_id_not_found(get_db_session_mock):
    """Raises HTTPException when routine not found"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        get_routine_by_id(db=get_db_session_mock, routine_id=999)
    
    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail


def test_get_routine_by_id_include_deleted(get_db_session_mock, existing_routine):
    """Successfully retrieves soft-deleted routine when include_deleted is True"""
    existing_routine.is_deleted = True
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine
    
    result = get_routine_by_id(db=get_db_session_mock, routine_id=1, include_deleted=True)
    
    assert result == existing_routine


def test_get_routines_success(get_db_session_mock, existing_routine):
    """Successfully retrieves all routines"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [existing_routine]
    get_db_session_mock.query.return_value = mock_query
    
    result = get_routines(db=get_db_session_mock)
    
    assert len(result) == 1


def test_get_routines_empty(get_db_session_mock):
    """Raises HTTPException when no routines found"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    get_db_session_mock.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc:
        get_routines(db=get_db_session_mock)
    
    assert exc.value.status_code == 404


def test_get_routines_by_patient_id_success(get_db_session_mock, existing_routine):
    """Successfully retrieves routines by patient ID"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [existing_routine]
    get_db_session_mock.query.return_value = mock_query
    
    result = get_routines_by_patient_id(db=get_db_session_mock, patient_id=1)
    
    assert len(result) == 1


def test_get_routines_by_patient_id_not_found(get_db_session_mock):
    """Raises HTTPException when no routines for patient"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []
    get_db_session_mock.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc:
        get_routines_by_patient_id(db=get_db_session_mock, patient_id=999)
    
    assert exc.value.status_code == 404


# ===== UPDATE tests =====

@patch("app.crud.routine_crud._validate_routine_data")
@patch("app.crud.routine_crud._check_for_duplicate_routine")
def test_update_routine_success(
    mock_check_duplicate, mock_validate,
    get_db_session_mock, mock_supervisor_user, update_routine_schema, 
    existing_routine
):
    """Successfully updates routine"""
    mock_check_duplicate.return_value = None
    mock_validate.return_value = None
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine
    
    result = update_routine(
        db=get_db_session_mock,
        routine_data=update_routine_schema,
        current_user_info=mock_supervisor_user
    )
    
    get_db_session_mock.commit.assert_called_once()
    mock_check_duplicate.assert_called_once()
    mock_validate.assert_called_once()


def test_update_routine_not_found(get_db_session_mock, mock_supervisor_user, update_routine_schema):
    """Raises HTTPException when routine not found"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        update_routine(
            db=get_db_session_mock,
            routine_data=update_routine_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 404


def test_update_routine_duplicate_detected(get_db_session_mock, base_routine_data, existing_routine):
    """Raises HTTPException when update creates a duplicate"""
    data = {**base_routine_data, "id": 1, "day_of_week": 3, "modified_by_id": "2"}
    schema = RoutineUpdate(**data)
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine
    
    with pytest.raises(HTTPException) as exc:
        _check_for_duplicate_routine(db=get_db_session_mock, routine_data=schema, exclude_id=1)
    
    assert exc.value.status_code == 409


# ===== DELETE tests =====

def test_delete_routine_success(
    get_db_session_mock, mock_supervisor_user, existing_routine
):
    """Successfully soft deletes routine"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine
    
    result = delete_routine(
        db=get_db_session_mock,
        routine_id=1,
        current_user_info=mock_supervisor_user
    )
    
    assert existing_routine.is_deleted
    get_db_session_mock.commit.assert_called_once()


def test_delete_routine_not_found(get_db_session_mock, mock_supervisor_user):
    """Raises HTTPException when routine not found"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        delete_routine(
            db=get_db_session_mock,
            routine_id=999,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 404


# ===== Helper Function tests =====

@patch("app.crud.routine_crud.get_patient_by_id")
@patch("app.crud.routine_crud.get_activity_by_id")
def test_validate_routine_data_success(
    mock_get_activity, mock_get_patient,
    get_db_session_mock, create_routine_schema, existing_activity
):
    """Validates routine data with valid inputs"""
    mock_get_activity.return_value = existing_activity
    mock_get_patient.return_value = {"patientId": 1}

    # Should not raise any exception
    _validate_routine_data(
        db=get_db_session_mock,
        routine_data=create_routine_schema,
        bearer_token="valid-token"
    )

    mock_get_activity.assert_called_once_with(get_db_session_mock, activity_id=create_routine_schema.activity_id)
    mock_get_patient.assert_called_once()


@patch("app.crud.routine_crud.get_activity_by_id")
def test_validate_routine_data_activity_not_found(
    mock_get_activity, get_db_session_mock, create_routine_schema
):
    """Raises HTTPException when activity not found"""
    mock_get_activity.return_value = None

    with pytest.raises(HTTPException) as exc:
        _validate_routine_data(
            db=get_db_session_mock,
            routine_data=create_routine_schema,
            bearer_token="valid-token"
        )

    assert exc.value.status_code == 404
    assert "Activity" in exc.value.detail


@patch("app.crud.routine_crud.get_activity_by_id")
def test_validate_routine_data_activity_deleted(
    mock_get_activity, get_db_session_mock, create_routine_schema, existing_activity
):
    """Raises HTTPException when activity is deleted"""
    existing_activity.is_deleted = True
    mock_get_activity.return_value = existing_activity

    with pytest.raises(HTTPException) as exc:
        _validate_routine_data(
            db=get_db_session_mock,
            routine_data=create_routine_schema,
            bearer_token="valid-token"
        )

    assert exc.value.status_code == 400
    assert "deleted activity" in exc.value.detail


@patch("app.crud.routine_crud.get_patient_by_id")
@patch("app.crud.routine_crud.get_activity_by_id")
def test_validate_routine_data_invalid_patient(
    mock_get_activity, mock_get_patient,
    get_db_session_mock, create_routine_schema, existing_activity
):
    """Raises HTTPException with invalid patient ID"""
    mock_get_activity.return_value = existing_activity
    mock_get_patient.side_effect = HTTPException(status_code=404, detail="Patient not found")

    with pytest.raises(HTTPException) as exc:
        _validate_routine_data(
            db=get_db_session_mock,
            routine_data=create_routine_schema,
            bearer_token="valid-token"
        )

    assert exc.value.status_code == 400
    assert "Invalid Patient ID" in exc.value.detail


@patch("app.crud.routine_crud.get_patient_by_id")
@patch("app.crud.routine_crud.get_activity_by_id")
def test_validate_routine_data_patient_service_unavailable(
    mock_get_activity, mock_get_patient,
    get_db_session_mock, create_routine_schema, existing_activity
):
    """Raises HTTPException when patient service is unavailable"""
    mock_get_activity.return_value = existing_activity
    mock_get_patient.side_effect = HTTPException(status_code=503, detail="Service unavailable")

    with pytest.raises(HTTPException) as exc:
        _validate_routine_data(
            db=get_db_session_mock,
            routine_data=create_routine_schema,
            bearer_token="valid-token"
        )

    assert exc.value.status_code == 400
    assert "Invalid Patient ID" in exc.value.detail


@patch("app.crud.routine_crud.get_patient_by_id")
@patch("app.crud.routine_crud.get_activity_by_id")
def test_validate_routine_data_bearer_token_passed(
    mock_get_activity, mock_get_patient,
    get_db_session_mock, create_routine_schema, existing_activity
):
    """Validates bearer token is correctly passed"""
    mock_get_activity.return_value = existing_activity
    mock_get_patient.return_value = {"patientId": 1}

    bearer_token = "test-bearer-token-123"

    _validate_routine_data(
        db=get_db_session_mock,
        routine_data=create_routine_schema,
        bearer_token=bearer_token
    )

    # Verify bearer token was passed correctly
    mock_get_patient.assert_called_once_with(
        require_auth=True,
        bearer_token=bearer_token,
        patient_id=create_routine_schema.patient_id,
    )


def test_check_for_duplicate_routine_overlapping_times(get_db_session_mock, base_routine_data, existing_routine):
    """Detects overlapping time ranges"""
    # existing: 9:00-10:00
    # new: 9:30-10:30 - overlaps
    data = {**base_routine_data, "start_time": time(9, 30), "end_time": time(10, 30)}
    schema = RoutineCreate(**data)
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine
    
    with pytest.raises(HTTPException) as exc:
        _check_for_duplicate_routine(db=get_db_session_mock, routine_data=schema)
    
    assert exc.value.status_code == 409


def test_check_for_duplicate_routine_non_overlapping_times(get_db_session_mock, base_routine_data):
    """Allows non-overlapping time ranges"""
    # existing: 9:00-10:00
    # new: 11:00-12:00 - no overlap
    data = {**base_routine_data, "start_time": time(11, 0), "end_time": time(12, 0)}
    schema = RoutineCreate(**data)
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    # Should not raise
    _check_for_duplicate_routine(db=get_db_session_mock, routine_data=schema)


def test_check_for_duplicate_routine_non_overlapping_dates(get_db_session_mock, base_routine_data):
    """Allows non-overlapping date ranges"""
    # existing: today+1 to today+30
    # new: today+60 to today+90 - no overlap
    data = {
        **base_routine_data,
        "start_date": date.today() + timedelta(days=60),
        "end_date": date.today() + timedelta(days=90)
    }
    schema = RoutineCreate(**data)
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    # Should not raise
    _check_for_duplicate_routine(db=get_db_session_mock, routine_data=schema)


# ===== Router tests - Testing role-based access control =====

@patch("app.routers.routine_router.crud.create_routine")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_create_routine_role_access(
    mock_crud_create, get_db_session_mock, mock_user_fixtures, request, 
    create_routine_schema, existing_routine
):
    """Tests that supervisors can create routines"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_create.return_value = existing_routine

    result = router_create_routine(
        db=get_db_session_mock,
        routine=create_routine_schema,
        user_and_token=(mock_user_roles, "test-token")
    )

    assert result is not None
    assert result == existing_routine

@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_create_routine_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request, create_routine_schema
):
    """Fails when non-supervisor tries to create routines"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_create_routine(
            db=get_db_session_mock,
            routine=create_routine_schema,
            user_and_token=(mock_user_roles, "test-token")
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in exc_info.value.detail.lower()

@patch("app.routers.routine_router.crud.get_routines")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_list_routines_role_access(
    mock_crud_get_routines, get_db_session_mock, existing_routines,
    mock_user_fixtures, request
):
    """Tests that supervisors can list routines"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get_routines.return_value = existing_routines

    result = router_list_routines(
        db=get_db_session_mock,
        current_user=mock_user_roles,
        skip=0,
        limit=100,
        include_deleted=False
    )

    assert result is not None
    assert result == existing_routines

@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_list_routines_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request
):
    """Fails when non-supervisor tries to list routines"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_list_routines(
            db=get_db_session_mock,
            current_user=mock_user_roles,
            skip=0,
            limit=100,
            include_deleted=False
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

@patch("app.routers.routine_router.crud.get_routine_by_id")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_get_routine_by_id_role_access(
    mock_crud_get_routine, get_db_session_mock, existing_routine,
    mock_user_fixtures, request
):
    """Tests that supervisors can get routine by ID"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get_routine.return_value = existing_routine

    result = router_get_routine_by_id(
        db=get_db_session_mock,
        routine_id=1,
        current_user=mock_user_roles,
        include_deleted=False
    )

    assert result is not None
    assert result == existing_routine


@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_get_routine_by_id_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request
):
    """Fails when non-supervisor tries to get routine by ID"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_get_routine_by_id(
            db=get_db_session_mock,
            routine_id=1,
            current_user=mock_user_roles,
            include_deleted=False
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

@patch("app.routers.routine_router.crud.update_routine")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_update_routine_role_access(
    mock_crud_update, get_db_session_mock, mock_user_fixtures, request,
    update_routine_schema, existing_routine
):
    """Tests that supervisors can update routines"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_update.return_value = existing_routine

    result = router_update_routine(
        db=get_db_session_mock,
        routine=update_routine_schema,
        user_and_token=(mock_user_roles, "test-token")
    )

    assert result is not None
    assert result == existing_routine

@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_update_routine_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request, update_routine_schema
):
    """Fails when non-supervisor tries to update routines"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_update_routine(
            db=get_db_session_mock,
            routine=update_routine_schema,
                user_and_token=(mock_user_roles, "test-token")
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

@patch("app.routers.routine_router.crud.delete_routine")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_delete_routine_role_access(
    mock_crud_delete, get_db_session_mock, existing_routine,
    mock_user_fixtures, request
):
    """Tests that supervisors can delete routines"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_delete.return_value = existing_routine

    result = router_delete_routine(
        db=get_db_session_mock,
        routine_id=1,
        current_user=mock_user_roles
    )

    assert result is not None
    assert result == existing_routine

@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_delete_routine_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request
):
    """Fails when non-supervisor tries to delete routines"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)

    with pytest.raises(HTTPException) as exc_info:
        router_delete_routine(
            db=get_db_session_mock,
            routine_id=1,
            current_user=mock_user_roles
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

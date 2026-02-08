import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from fastapi import HTTPException, status
from pydantic import ValidationError
from app.schemas.routine_exclusion_schema import (
    RoutineExclusionCreate,
    RoutineExclusionUpdate,
)
from app.crud.routine_exclusion_crud import (
    create_routine_exclusion,
    get_routine_exclusion_by_id,
    get_routine_exclusions,
    get_routine_exclusions_by_routine_id,
    update_routine_exclusion,
    delete_routine_exclusion,
    _check_for_overlapping_exclusion,
    _validate_routine_exclusion_data,
)
from app.routers.routine_exclusion_router import (
    create_routine_exclusion as router_create_routine_exclusion,
    list_routine_exclusions as router_list_routine_exclusions,
    get_routine_exclusion_by_id as router_get_routine_exclusion_by_id,
    list_routine_exclusions_by_routine as router_list_routine_exclusions_by_routine,
    update_routine_exclusion as router_update_routine_exclusion,
    delete_routine_exclusion as router_delete_routine_exclusion,
)


@pytest.fixture(autouse=True)
def disable_crud_logging(monkeypatch):
    """Auto-disable CRUD logging to prevent JSON serialization issues with MagicMocks"""
    from app.crud import routine_exclusion_crud
    monkeypatch.setattr(routine_exclusion_crud, "log_crud_action", lambda *args, **kwargs: None)


@pytest.fixture
def create_routine_exclusion_schema(base_routine_exclusion_data):
    """RoutineExclusionCreate schema instance"""
    return RoutineExclusionCreate(**base_routine_exclusion_data)


@pytest.fixture
def update_routine_exclusion_schema(base_routine_exclusion_data_list):
    """RoutineExclusionUpdate schema instance"""
    data = base_routine_exclusion_data_list[1].copy()
    data['id'] = 1
    return RoutineExclusionUpdate(**data)


# ===== Schema Validation Tests =====

@pytest.mark.parametrize(
    "override_fields, expected_error",
    [
        # start_date >= end_date
        ({"start_date": date.today() + timedelta(days=30), "end_date": date.today() + timedelta(days=1)}, "start_date must be before end_date"),
        ({"start_date": date.today() + timedelta(days=10), "end_date": date.today() + timedelta(days=10)}, "start_date must be before end_date"),
    ]
)
def test_routine_exclusion_create_validation_fails(base_routine_exclusion_data, override_fields, expected_error):
    """Raises ValidationError with invalid data for RoutineExclusionCreate"""
    data = {**base_routine_exclusion_data, **override_fields}
    
    with pytest.raises(ValidationError) as exc:
        RoutineExclusionCreate(**data)
    
    assert expected_error in str(exc.value)


def test_routine_exclusion_create_validation_passes(base_routine_exclusion_data):
    """Successfully creates RoutineExclusionCreate schema with valid data"""
    schema = RoutineExclusionCreate(**base_routine_exclusion_data)
    assert schema.routine_id == base_routine_exclusion_data["routine_id"]
    assert schema.start_date == base_routine_exclusion_data["start_date"]
    assert schema.end_date == base_routine_exclusion_data["end_date"]


# ===== CREATE tests =====

@patch("app.crud.routine_exclusion_crud.get_routine_by_id")
def test_create_routine_exclusion_success(
    mock_get_routine, get_db_session_mock, mock_supervisor_user,
    create_routine_exclusion_schema, existing_routine
):
    """Creates routine exclusion when all validations pass"""
    mock_get_routine.return_value = existing_routine
    
    # No overlapping exclusion found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    result = create_routine_exclusion(
        db=get_db_session_mock,
        exclusion_data=create_routine_exclusion_schema,
        current_user_info=mock_supervisor_user
    )
    
    get_db_session_mock.add.assert_called_once()
    get_db_session_mock.commit.assert_called_once()
    
    for field in create_routine_exclusion_schema.model_fields:
        if field != 'remarks' or create_routine_exclusion_schema.remarks is not None:
            assert getattr(result, field) == getattr(create_routine_exclusion_schema, field), f"Mismatch on field: {field}"


@patch("app.crud.routine_exclusion_crud.get_routine_by_id")
def test_create_routine_exclusion_routine_not_found(
    mock_get_routine, get_db_session_mock, mock_supervisor_user, create_routine_exclusion_schema
):
    """Raises HTTPException when routine not found"""
    mock_get_routine.return_value = None
    
    # No overlapping exclusion found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        create_routine_exclusion(
            db=get_db_session_mock,
            exclusion_data=create_routine_exclusion_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 404
    assert "Routine with ID" in exc.value.detail


@patch("app.crud.routine_exclusion_crud.get_routine_by_id")
def test_create_routine_exclusion_routine_deleted(
    mock_get_routine, get_db_session_mock, mock_supervisor_user,
    create_routine_exclusion_schema, existing_routine
):
    """Raises HTTPException when routine is deleted"""
    existing_routine.is_deleted = True
    mock_get_routine.return_value = existing_routine
    
    # No overlapping exclusion found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        create_routine_exclusion(
            db=get_db_session_mock,
            exclusion_data=create_routine_exclusion_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 400
    assert "deleted routine" in exc.value.detail


def test_create_routine_exclusion_overlapping_detected(
    get_db_session_mock, mock_supervisor_user, create_routine_exclusion_schema, existing_routine_exclusion
):
    """Raises HTTPException when overlapping exclusion exists"""
    # Overlapping exclusion found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine_exclusion
    
    with pytest.raises(HTTPException) as exc:
        create_routine_exclusion(
            db=get_db_session_mock,
            exclusion_data=create_routine_exclusion_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 409
    assert "overlapping" in exc.value.detail


def test_create_routine_exclusion_db_error(
    get_db_session_mock, mock_supervisor_user, create_routine_exclusion_schema, existing_routine
):
    """Raises HTTPException when database error occurs"""
    with patch("app.crud.routine_exclusion_crud.get_routine_by_id", return_value=existing_routine):
        get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
        get_db_session_mock.commit.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc:
            create_routine_exclusion(
                db=get_db_session_mock,
                exclusion_data=create_routine_exclusion_schema,
                current_user_info=mock_supervisor_user
            )
        
        assert exc.value.status_code == 500
        assert "Error creating" in exc.value.detail


# ===== GET tests =====

def test_get_routine_exclusion_by_id_success(get_db_session_mock, existing_routine_exclusion):
    """Successfully retrieves routine exclusion by ID"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine_exclusion
    
    result = get_routine_exclusion_by_id(db=get_db_session_mock, exclusion_id=1)
    
    assert result == existing_routine_exclusion


def test_get_routine_exclusion_by_id_not_found(get_db_session_mock):
    """Raises HTTPException when exclusion not found"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        get_routine_exclusion_by_id(db=get_db_session_mock, exclusion_id=999)
    
    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail


def test_get_routine_exclusion_by_id_include_deleted(get_db_session_mock, existing_routine_exclusion):
    """Successfully retrieves soft-deleted exclusion when include_deleted is True"""
    existing_routine_exclusion.is_deleted = True
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine_exclusion
    
    result = get_routine_exclusion_by_id(db=get_db_session_mock, exclusion_id=1, include_deleted=True)
    
    assert result == existing_routine_exclusion
    assert result.is_deleted


def test_get_routine_exclusions_success(get_db_session_mock, existing_routine_exclusion):
    """Successfully retrieves all routine exclusions"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [existing_routine_exclusion]
    get_db_session_mock.query.return_value = mock_query
    
    result = get_routine_exclusions(db=get_db_session_mock)
    
    assert len(result) == 1


def test_get_routine_exclusions_empty(get_db_session_mock):
    """Raises HTTPException when no exclusions found"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    get_db_session_mock.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc:
        get_routine_exclusions(db=get_db_session_mock)
    
    assert exc.value.status_code == 404


def test_get_routine_exclusions_with_pagination(get_db_session_mock, existing_routine_exclusion):
    """Successfully retrieves exclusions with pagination parameters"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = [existing_routine_exclusion]
    get_db_session_mock.query.return_value = mock_query
    
    result = get_routine_exclusions(db=get_db_session_mock, skip=5, limit=10)
    
    assert len(result) == 1
    mock_query.offset.assert_called_with(5)
    mock_query.limit.assert_called_with(10)


def test_get_routine_exclusions_by_routine_id_success(get_db_session_mock, existing_routine_exclusion):
    """Successfully retrieves exclusions by routine ID"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [existing_routine_exclusion]
    get_db_session_mock.query.return_value = mock_query
    
    result = get_routine_exclusions_by_routine_id(db=get_db_session_mock, routine_id=1)
    
    assert len(result) == 1


def test_get_routine_exclusions_by_routine_id_not_found(get_db_session_mock):
    """Raises HTTPException when no exclusions found for routine"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []
    get_db_session_mock.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc:
        get_routine_exclusions_by_routine_id(db=get_db_session_mock, routine_id=999)
    
    assert exc.value.status_code == 404
    assert "No Routine Exclusion records for this routine" in exc.value.detail


# ===== UPDATE tests =====

@patch("app.crud.routine_exclusion_crud._validate_routine_exclusion_data")
@patch("app.crud.routine_exclusion_crud._check_for_overlapping_exclusion")
def test_update_routine_exclusion_success(
    mock_check_overlap, mock_validate, get_db_session_mock, mock_supervisor_user, 
    update_routine_exclusion_schema, existing_routine_exclusion
):
    """Successfully updates routine exclusion"""
    mock_validate.return_value = None
    mock_check_overlap.return_value = None
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine_exclusion
    
    result = update_routine_exclusion(
        db=get_db_session_mock,
        exclusion_data=update_routine_exclusion_schema,
        current_user_info=mock_supervisor_user
    )
    
    get_db_session_mock.commit.assert_called_once()
    mock_validate.assert_called_once()
    mock_check_overlap.assert_called_once()
    assert result.modified_by_id == mock_supervisor_user["id"]


def test_update_routine_exclusion_not_found(get_db_session_mock, mock_supervisor_user, update_routine_exclusion_schema):
    """Raises HTTPException when exclusion not found"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        update_routine_exclusion(
            db=get_db_session_mock,
            exclusion_data=update_routine_exclusion_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 404


@patch("app.crud.routine_exclusion_crud._validate_routine_exclusion_data")
def test_update_routine_exclusion_overlapping_detected(
    mock_validate, get_db_session_mock, mock_supervisor_user,
    update_routine_exclusion_schema, existing_routine_exclusion
):
    """Raises HTTPException when update creates overlapping exclusion"""
    mock_validate.return_value = None
    
    get_db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        existing_routine_exclusion,  # First call: get exclusion to update
        existing_routine_exclusion,  # Second call: overlapping check
    ]
    
    with pytest.raises(HTTPException) as exc:
        update_routine_exclusion(
            db=get_db_session_mock,
            exclusion_data=update_routine_exclusion_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 409
    assert "overlapping" in exc.value.detail


@patch("app.crud.routine_exclusion_crud._validate_routine_exclusion_data")
@patch("app.crud.routine_exclusion_crud._check_for_overlapping_exclusion")
def test_update_routine_exclusion_db_error(
    mock_check_overlap, mock_validate, get_db_session_mock, mock_supervisor_user, update_routine_exclusion_schema, existing_routine_exclusion
):
    """Raises HTTPException when database error occurs"""
    mock_validate.return_value = None
    mock_check_overlap.return_value = None
    
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine_exclusion
    get_db_session_mock.commit.side_effect = Exception("Database error")
    
    with pytest.raises(HTTPException) as exc:
        update_routine_exclusion(
            db=get_db_session_mock,
            exclusion_data=update_routine_exclusion_schema,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 500
    assert "Error updating" in exc.value.detail


# ===== DELETE tests =====

def test_delete_routine_exclusion_success(
    get_db_session_mock, mock_supervisor_user, existing_routine_exclusion
):
    """Successfully soft deletes routine exclusion"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine_exclusion
    
    result = delete_routine_exclusion(
        db=get_db_session_mock,
        exclusion_id=1,
        current_user_info=mock_supervisor_user
    )
    
    assert existing_routine_exclusion.is_deleted
    get_db_session_mock.commit.assert_called_once()
    assert result.modified_by_id == mock_supervisor_user["id"]


def test_delete_routine_exclusion_not_found(get_db_session_mock, mock_supervisor_user):
    """Raises HTTPException when exclusion not found"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        delete_routine_exclusion(
            db=get_db_session_mock,
            exclusion_id=999,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 404


def test_delete_routine_exclusion_db_error(
    get_db_session_mock, mock_supervisor_user, existing_routine_exclusion
):
    """Raises HTTPException when database error occurs"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine_exclusion
    get_db_session_mock.commit.side_effect = Exception("Database error")
    
    with pytest.raises(HTTPException) as exc:
        delete_routine_exclusion(
            db=get_db_session_mock,
            exclusion_id=1,
            current_user_info=mock_supervisor_user
        )
    
    assert exc.value.status_code == 500
    assert "Error deleting" in exc.value.detail


# ===== Helper Function tests =====

@patch("app.crud.routine_exclusion_crud.get_routine_by_id")
def test_validate_routine_exclusion_data_success(
    mock_get_routine, get_db_session_mock, create_routine_exclusion_schema, existing_routine
):
    """Validates exclusion data with valid inputs"""
    mock_get_routine.return_value = existing_routine
    
    # Should not raise any exception
    _validate_routine_exclusion_data(
        db=get_db_session_mock,
        exclusion_data=create_routine_exclusion_schema
    )
    
    mock_get_routine.assert_called_once_with(get_db_session_mock, routine_id=create_routine_exclusion_schema.routine_id)


@patch("app.crud.routine_exclusion_crud.get_routine_by_id")
def test_validate_routine_exclusion_data_routine_not_found(
    mock_get_routine, get_db_session_mock, create_routine_exclusion_schema
):
    """Raises HTTPException when routine not found"""
    mock_get_routine.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        _validate_routine_exclusion_data(
            db=get_db_session_mock,
            exclusion_data=create_routine_exclusion_schema
        )
    
    assert exc.value.status_code == 404
    assert "Routine with ID" in exc.value.detail


@patch("app.crud.routine_exclusion_crud.get_routine_by_id")
def test_validate_routine_exclusion_data_routine_deleted(
    mock_get_routine, get_db_session_mock, create_routine_exclusion_schema, existing_routine
):
    """Raises HTTPException when routine is deleted"""
    existing_routine.is_deleted = True
    mock_get_routine.return_value = existing_routine
    
    with pytest.raises(HTTPException) as exc:
        _validate_routine_exclusion_data(
            db=get_db_session_mock,
            exclusion_data=create_routine_exclusion_schema
        )
    
    assert exc.value.status_code == 400
    assert "deleted routine" in exc.value.detail


def test_check_for_overlapping_exclusion_not_found(
    get_db_session_mock, create_routine_exclusion_schema
):
    """Should not raise when no overlapping exclusion found"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None
    
    # Should not raise
    _check_for_overlapping_exclusion(db=get_db_session_mock, exclusion_data=create_routine_exclusion_schema)


def test_check_for_overlapping_exclusion_found(
    get_db_session_mock, create_routine_exclusion_schema, existing_routine_exclusion
):
    """Raises HTTPException when overlapping exclusion found"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_routine_exclusion
    
    with pytest.raises(HTTPException) as exc:
        _check_for_overlapping_exclusion(db=get_db_session_mock, exclusion_data=create_routine_exclusion_schema)
    
    assert exc.value.status_code == 409
    assert "overlapping" in exc.value.detail


def test_check_for_overlapping_exclusion_exclude_self(
    get_db_session_mock, create_routine_exclusion_schema
):
    """Should not consider self when checking for overlap with exclude_id"""
    mock_query = MagicMock()
    mock_filter_chain = MagicMock()
    mock_filter_chain.filter.return_value.first.return_value = None
    mock_query.filter.return_value = mock_filter_chain
    get_db_session_mock.query.return_value = mock_query
    
    # Should not raise even if exclude_id is provided
    _check_for_overlapping_exclusion(
        db=get_db_session_mock,
        exclusion_data=create_routine_exclusion_schema,
        exclude_id=1
    )


# ===== Router tests - Testing role-based access control =====

@patch("app.routers.routine_exclusion_router.crud.create_routine_exclusion")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_create_routine_exclusion_role_access(
    mock_crud_create, get_db_session_mock, mock_user_fixtures, request, 
    create_routine_exclusion_schema, existing_routine_exclusion
):
    """Tests that supervisors can create routine exclusions"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_create.return_value = existing_routine_exclusion
    
    result = router_create_routine_exclusion(
        db=get_db_session_mock,
        exclusion=create_routine_exclusion_schema,
        user_and_token=(mock_user_roles, "test-token")
    )
    
    assert result is not None
    assert result == existing_routine_exclusion


@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_create_routine_exclusion_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request, create_routine_exclusion_schema
):
    """Fails when non-supervisor tries to create routine exclusions"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_create_routine_exclusion(
            db=get_db_session_mock,
            exclusion=create_routine_exclusion_schema,
            user_and_token=(mock_user_roles, "test-token")
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in exc_info.value.detail.lower()


@patch("app.routers.routine_exclusion_router.crud.get_routine_exclusions")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_list_routine_exclusions_role_access(
    mock_crud_get, get_db_session_mock, existing_routine_exclusion,
    mock_user_fixtures, request
):
    """Tests that supervisors can list routine exclusions"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get.return_value = [existing_routine_exclusion]
    
    result = router_list_routine_exclusions(
        db=get_db_session_mock,
        current_user=mock_user_roles,
        skip=0,
        limit=100,
        include_deleted=False
    )
    
    assert result is not None
    assert len(result) == 1


@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_list_routine_exclusions_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request
):
    """Fails when non-supervisor tries to list routine exclusions"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_list_routine_exclusions(
            db=get_db_session_mock,
            current_user=mock_user_roles,
            include_deleted=False,
            skip=0,
            limit=100
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in exc_info.value.detail.lower()


@patch("app.routers.routine_exclusion_router.crud.get_routine_exclusion_by_id")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_get_routine_exclusion_by_id_role_access(
    mock_crud_get, get_db_session_mock, existing_routine_exclusion,
    mock_user_fixtures, request
):
    """Tests that supervisors can retrieve routine exclusions by ID"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get.return_value = existing_routine_exclusion
    
    result = router_get_routine_exclusion_by_id(
        db=get_db_session_mock,
        exclusion_id=1,
        current_user=mock_user_roles,
        include_deleted=False
    )
    
    assert result is not None
    assert result == existing_routine_exclusion


@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_get_routine_exclusion_by_id_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request
):
    """Fails when non-supervisor tries to get routine exclusions by ID"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_get_routine_exclusion_by_id(
            db=get_db_session_mock,
            exclusion_id=1,
            include_deleted=False,
            current_user=mock_user_roles
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in exc_info.value.detail.lower()


@patch("app.routers.routine_exclusion_router.crud.get_routine_exclusions_by_routine_id")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_list_routine_exclusions_by_routine_role_access(
    mock_crud_get, get_db_session_mock, existing_routine_exclusion,
    mock_user_fixtures, request
):
    """Tests that supervisors can list routine exclusions by routine ID"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_get.return_value = [existing_routine_exclusion]
    
    result = router_list_routine_exclusions_by_routine(
        db=get_db_session_mock,
        routine_id=1,
        current_user=mock_user_roles,
        include_deleted=False
    )
    
    assert result is not None
    assert len(result) == 1


@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_list_routine_exclusions_by_routine_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request
):
    """Fails when non-supervisor tries to list routine exclusions by routine"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_list_routine_exclusions_by_routine(
            db=get_db_session_mock,
            routine_id=1,
            include_deleted=False,
            current_user=mock_user_roles
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in exc_info.value.detail.lower()


@patch("app.routers.routine_exclusion_router.crud.update_routine_exclusion")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_update_routine_exclusion_role_access(
    mock_crud_update, get_db_session_mock, mock_user_fixtures, request,
    update_routine_exclusion_schema, existing_routine_exclusion
):
    """Tests that supervisors can update routine exclusions"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_update.return_value = existing_routine_exclusion
    
    result = router_update_routine_exclusion(
        db=get_db_session_mock,
        exclusion=update_routine_exclusion_schema,
        user_and_token=(mock_user_roles, "test-token")
    )
    
    assert result is not None
    assert result == existing_routine_exclusion


@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_update_routine_exclusion_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request, update_routine_exclusion_schema
):
    """Fails when non-supervisor tries to update routine exclusions"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_update_routine_exclusion(
            db=get_db_session_mock,
            exclusion=update_routine_exclusion_schema,
            user_and_token=(mock_user_roles, "test-token")
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in exc_info.value.detail.lower()


@patch("app.routers.routine_exclusion_router.crud.delete_routine_exclusion")
@pytest.mark.parametrize("mock_user_fixtures", ["mock_supervisor_jwt"])
def test_delete_routine_exclusion_role_access(
    mock_crud_delete, get_db_session_mock, mock_user_fixtures, request, existing_routine_exclusion
):
    """Tests that supervisors can delete routine exclusions"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    mock_crud_delete.return_value = existing_routine_exclusion
    
    result = router_delete_routine_exclusion(
        db=get_db_session_mock,
        exclusion_id=1,
        current_user=mock_user_roles
    )
    
    assert result is not None
    assert result == existing_routine_exclusion


@pytest.mark.parametrize("mock_user_fixtures", ["mock_caregiver_jwt", "mock_doctor_jwt", "mock_admin_jwt"])
def test_delete_routine_exclusion_role_access_fail(
    get_db_session_mock, mock_user_fixtures, request
):
    """Fails when non-supervisor tries to delete routine exclusions"""
    mock_user_roles = request.getfixturevalue(mock_user_fixtures)
    
    with pytest.raises(HTTPException) as exc_info:
        router_delete_routine_exclusion(
            db=get_db_session_mock,
            exclusion_id=1,
            current_user=mock_user_roles
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in exc_info.value.detail.lower()

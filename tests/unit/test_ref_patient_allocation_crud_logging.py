from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.crud import ref_patient_allocation_crud
from app.logger.logger_utils import ActionType
from app.models.ref_patient_allocation_model import RefPatientAllocation
from app.schemas.ref_patient_allocation import (
    RefPatientAllocationCreate,
    RefPatientAllocationUpdate,
    RefPatientAllocationDelete,
)


@pytest.fixture
def mock_log_crud_action(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(ref_patient_allocation_crud, "log_crud_action", mock)
    return mock


@pytest.fixture
def bypass_idempotency(monkeypatch):
    """Run the operation immediately and report it as not-a-duplicate, mirroring
    IdempotencyService.process_idempotent's success path without touching the DB."""
    def fake_process_idempotent(db, correlation_id, event_type, aggregate_id, processed_by, operation):
        return operation(), False

    monkeypatch.setattr(
        ref_patient_allocation_crud.IdempotencyService, "process_idempotent", fake_process_idempotent
    )


def _make_allocation(**overrides):
    data = dict(
        id=1,
        active="Y",
        isDeleted="0",
        patientId=10,
        doctorId="doc-1",
        gameTherapistId="gt-1",
        supervisorId="sup-1",
        caregiverId="care-1",
        tempDoctorId=None,
        tempCaregiverId=None,
        created_date=datetime(2024, 1, 1),
        modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service",
        modified_by_id="patient_service",
    )
    data.update(overrides)
    return RefPatientAllocation(**data)


def test_create_ref_patient_allocation_logs_create_action(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    created_allocation = _make_allocation()
    db.query.return_value.filter.return_value.first.side_effect = [None, created_allocation]

    allocation_in = RefPatientAllocationCreate(
        id=1,
        patient_id=10,
        doctor_id="doc-1",
        game_therapist_id="gt-1",
        supervisor_id="sup-1",
        caregiver_id="care-1",
        created_date=datetime(2024, 1, 1),
        modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service",
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_allocation_crud.create_ref_patient_allocation(
        db=db, allocation=allocation_in, correlation_id="corr-1", created_by="patient_service"
    )

    assert was_duplicate is False
    mock_log_crud_action.assert_called_once()
    _, kwargs = mock_log_crud_action.call_args
    assert kwargs["action"] == ActionType.CREATE
    assert kwargs["user"] == "patient_service"
    assert kwargs["user_full_name"] == "patient_service"
    assert kwargs["table"] == "REF_PATIENT_ALLOCATION"
    assert kwargs["entity_id"] == 1
    assert kwargs["original_data"] is None
    assert kwargs["updated_data"]["doctor_id"] == "doc-1"
    assert kwargs["log_type"] == "system"
    assert kwargs["is_system_config"] is True
    db.commit.assert_called_once()


def test_create_ref_patient_allocation_duplicate_does_not_log(mock_log_crud_action, monkeypatch):
    db = MagicMock()

    def fake_process_idempotent_duplicate(db, correlation_id, event_type, aggregate_id, processed_by, operation):
        return None, True

    monkeypatch.setattr(
        ref_patient_allocation_crud.IdempotencyService, "process_idempotent", fake_process_idempotent_duplicate
    )

    existing_allocation = MagicMock(spec=RefPatientAllocation)
    db.query.return_value.filter.return_value.first.return_value = existing_allocation

    allocation_in = RefPatientAllocationCreate(
        id=1,
        patient_id=10,
        doctor_id="doc-1",
        game_therapist_id="gt-1",
        supervisor_id="sup-1",
        caregiver_id="care-1",
        created_date=datetime(2024, 1, 1),
        modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service",
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_allocation_crud.create_ref_patient_allocation(
        db=db, allocation=allocation_in, correlation_id="corr-1", created_by="patient_service"
    )

    assert was_duplicate is True
    mock_log_crud_action.assert_not_called()


def test_update_ref_patient_allocation_logs_update_action(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db_allocation = _make_allocation()
    db.query.return_value.filter.return_value.first.return_value = db_allocation

    allocation_update = RefPatientAllocationUpdate(
        doctor_id="doc-2",
        modified_date=datetime(2024, 2, 1),
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_allocation_crud.update_ref_patient_allocation(
        db=db, allocation_id="1", allocation_update=allocation_update, correlation_id="corr-2"
    )

    assert was_duplicate is False
    assert result.doctorId == "doc-2"
    mock_log_crud_action.assert_called_once()
    _, kwargs = mock_log_crud_action.call_args
    assert kwargs["action"] == ActionType.UPDATE
    assert kwargs["user"] == "patient_service"
    assert kwargs["entity_id"] == 1
    assert kwargs["original_data"]["doctorId"] == "doc-1"
    assert kwargs["updated_data"]["doctor_id"] == "doc-2"
    db.commit.assert_called_once()


def test_update_ref_patient_allocation_not_found_does_not_log(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    allocation_update = RefPatientAllocationUpdate(
        doctor_id="doc-2",
        modified_date=datetime(2024, 2, 1),
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_allocation_crud.update_ref_patient_allocation(
        db=db, allocation_id="999", allocation_update=allocation_update, correlation_id="corr-3"
    )

    assert result is None
    mock_log_crud_action.assert_not_called()


def test_delete_ref_patient_allocation_logs_delete_action(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db_allocation = _make_allocation()
    db.query.return_value.filter.return_value.first.return_value = db_allocation

    allocation_delete = RefPatientAllocationDelete(
        modified_date=datetime(2024, 3, 1),
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_allocation_crud.delete_ref_patient_allocation(
        db=db, allocation_id="1", allocation_delete=allocation_delete, correlation_id="corr-4"
    )

    assert was_duplicate is False
    assert result.isDeleted == "1"
    mock_log_crud_action.assert_called_once()
    _, kwargs = mock_log_crud_action.call_args
    assert kwargs["action"] == ActionType.DELETE
    assert kwargs["user"] == "patient_service"
    assert kwargs["entity_id"] == 1
    assert kwargs["original_data"]["isDeleted"] == "0"
    assert kwargs["updated_data"] is None
    db.commit.assert_called_once()


def test_delete_ref_patient_allocation_already_deleted_does_not_log(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db_allocation = _make_allocation(isDeleted="1")
    db.query.return_value.filter.return_value.first.return_value = db_allocation

    allocation_delete = RefPatientAllocationDelete(
        modified_date=datetime(2024, 3, 1),
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_allocation_crud.delete_ref_patient_allocation(
        db=db, allocation_id="1", allocation_delete=allocation_delete, correlation_id="corr-5"
    )

    assert was_duplicate is False
    mock_log_crud_action.assert_not_called()

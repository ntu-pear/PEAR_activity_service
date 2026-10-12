from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.crud import ref_patient_crud
from app.logger.logger_utils import ActionType
from app.models import RefPatient
from app.schemas.ref_patient import RefPatientCreate, RefPatientUpdate, RefPatientDelete


@pytest.fixture
def mock_log_crud_action(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(ref_patient_crud, "log_crud_action", mock)
    return mock


@pytest.fixture
def bypass_idempotency(monkeypatch):
    """Run the operation immediately and report it as not-a-duplicate, mirroring
    IdempotencyService.process_idempotent's success path without touching the DB."""
    def fake_process_idempotent(db, correlation_id, event_type, aggregate_id, processed_by, operation):
        return operation(), False

    monkeypatch.setattr(
        ref_patient_crud.IdempotencyService, "process_idempotent", fake_process_idempotent
    )


def test_create_ref_patient_logs_create_action(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    created_patient = RefPatient(
        id=1,
        name="Alice",
        preferred_name=None,
        update_bit="1",
        start_date=datetime(2024, 1, 1),
        end_date=None,
        is_active="1",
        is_deleted="0",
        created_date=datetime(2024, 1, 1),
        modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service",
        modified_by_id="patient_service",
    )
    # First .first() call: "existing patient" check inside create_operation -> None
    # Second .first() call: fetch of the newly-created patient -> created_patient
    db.query.return_value.filter.return_value.first.side_effect = [None, created_patient]

    patient_in = RefPatientCreate(
        id=1,
        name="Alice",
        start_date=datetime(2024, 1, 1),
        created_date=datetime(2024, 1, 1),
        modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service",
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_crud.create_ref_patient(
        db=db, patient=patient_in, correlation_id="corr-1", created_by="patient_service"
    )

    assert was_duplicate is False
    mock_log_crud_action.assert_called_once()
    _, kwargs = mock_log_crud_action.call_args
    assert kwargs["action"] == ActionType.CREATE
    assert kwargs["user"] == "patient_service"
    assert kwargs["user_full_name"] == "patient_service"
    assert kwargs["table"] == "REF_PATIENT"
    assert kwargs["entity_id"] == 1
    assert kwargs["original_data"] is None
    assert kwargs["updated_data"]["name"] == "Alice"
    assert kwargs["patient_id"] == 1
    assert kwargs["patient_full_name"] == "Alice"
    assert kwargs["log_type"] == "system"
    assert kwargs["is_system_config"] is True
    db.commit.assert_called_once()


def test_create_ref_patient_duplicate_does_not_log(mock_log_crud_action, monkeypatch):
    db = MagicMock()

    def fake_process_idempotent_duplicate(db, correlation_id, event_type, aggregate_id, processed_by, operation):
        return None, True

    monkeypatch.setattr(ref_patient_crud.IdempotencyService, "process_idempotent", fake_process_idempotent_duplicate)

    existing_patient = MagicMock(spec=RefPatient)
    db.query.return_value.filter.return_value.first.return_value = existing_patient

    patient_in = RefPatientCreate(
        id=1,
        name="Alice",
        start_date=datetime(2024, 1, 1),
        created_date=datetime(2024, 1, 1),
        modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service",
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_crud.create_ref_patient(
        db=db, patient=patient_in, correlation_id="corr-1", created_by="patient_service"
    )

    assert was_duplicate is True
    mock_log_crud_action.assert_not_called()


def test_update_ref_patient_logs_update_action(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db_patient = RefPatient(
        id=1,
        name="Alice",
        preferred_name=None,
        update_bit="1",
        start_date=datetime(2024, 1, 1),
        end_date=None,
        is_active="1",
        is_deleted="0",
        created_date=datetime(2024, 1, 1),
        modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service",
        modified_by_id="patient_service",
    )
    db.query.return_value.filter.return_value.first.return_value = db_patient

    patient_update = RefPatientUpdate(
        name="Alice Updated",
        modified_date=datetime(2024, 2, 1),
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_crud.update_ref_patient(
        db=db, patient_id="1", patient_update=patient_update, correlation_id="corr-2"
    )

    assert was_duplicate is False
    assert result.name == "Alice Updated"
    mock_log_crud_action.assert_called_once()
    _, kwargs = mock_log_crud_action.call_args
    assert kwargs["action"] == ActionType.UPDATE
    assert kwargs["user"] == "patient_service"
    assert kwargs["entity_id"] == 1
    assert kwargs["original_data"]["name"] == "Alice"
    assert kwargs["updated_data"]["name"] == "Alice Updated"
    assert kwargs["patient_id"] == 1
    assert kwargs["patient_full_name"] == "Alice Updated"
    db.commit.assert_called_once()


def test_update_ref_patient_not_found_does_not_log(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    patient_update = RefPatientUpdate(
        name="Alice Updated",
        modified_date=datetime(2024, 2, 1),
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_crud.update_ref_patient(
        db=db, patient_id="999", patient_update=patient_update, correlation_id="corr-3"
    )

    assert result is None
    mock_log_crud_action.assert_not_called()


def test_delete_ref_patient_logs_delete_action(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db_patient = RefPatient(
        id=1,
        name="Alice",
        preferred_name=None,
        update_bit="1",
        start_date=datetime(2024, 1, 1),
        end_date=None,
        is_active="1",
        is_deleted="0",
        created_date=datetime(2024, 1, 1),
        modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service",
        modified_by_id="patient_service",
    )
    db.query.return_value.filter.return_value.first.return_value = db_patient

    patient_delete = RefPatientDelete(
        modified_date=datetime(2024, 3, 1),
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_crud.delete_ref_patient(
        db=db, patient_id="1", patient_delete=patient_delete, correlation_id="corr-4"
    )

    assert was_duplicate is False
    assert result.is_deleted == "1"
    mock_log_crud_action.assert_called_once()
    _, kwargs = mock_log_crud_action.call_args
    assert kwargs["action"] == ActionType.DELETE
    assert kwargs["user"] == "patient_service"
    assert kwargs["entity_id"] == 1
    assert kwargs["original_data"]["is_deleted"] == "0"
    assert kwargs["updated_data"] is None
    assert kwargs["patient_id"] == 1
    assert kwargs["patient_full_name"] == "Alice"
    db.commit.assert_called_once()


def test_delete_ref_patient_already_deleted_does_not_log(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db_patient = RefPatient(
        id=1,
        name="Alice",
        preferred_name=None,
        update_bit="1",
        start_date=datetime(2024, 1, 1),
        end_date=None,
        is_active="1",
        is_deleted="1",
        created_date=datetime(2024, 1, 1),
        modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service",
        modified_by_id="patient_service",
    )
    db.query.return_value.filter.return_value.first.return_value = db_patient

    patient_delete = RefPatientDelete(
        modified_date=datetime(2024, 3, 1),
        modified_by_id="patient_service",
    )

    result, was_duplicate = ref_patient_crud.delete_ref_patient(
        db=db, patient_id="1", patient_delete=patient_delete, correlation_id="corr-5"
    )

    assert was_duplicate is False
    mock_log_crud_action.assert_not_called()


def _commits_seen_at_log(mock_log, db):
    seen = []
    mock_log.side_effect = lambda *args, **kwargs: seen.append(db.commit.call_count)
    return seen


def _ref_patient():
    return RefPatient(
        id=1, name="Alice", preferred_name=None, update_bit="1",
        start_date=datetime(2024, 1, 1), end_date=None, is_active="1", is_deleted="0",
        created_date=datetime(2024, 1, 1), modified_date=datetime(2024, 1, 1),
        created_by_id="patient_service", modified_by_id="patient_service",
    )


def test_create_ref_patient_logs_after_commit(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [None, _ref_patient()]
    seen = _commits_seen_at_log(mock_log_crud_action, db)

    ref_patient_crud.create_ref_patient(
        db=db,
        patient=RefPatientCreate(
            id=1, name="Alice", start_date=datetime(2024, 1, 1),
            created_date=datetime(2024, 1, 1), modified_date=datetime(2024, 1, 1),
            created_by_id="patient_service", modified_by_id="patient_service",
        ),
        correlation_id="corr-6",
        created_by="patient_service",
    )

    assert seen == [1]


def test_update_ref_patient_logs_after_commit(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _ref_patient()
    seen = _commits_seen_at_log(mock_log_crud_action, db)

    ref_patient_crud.update_ref_patient(
        db=db,
        patient_id="1",
        patient_update=RefPatientUpdate(
            name="Alice Updated", modified_date=datetime(2024, 2, 1), modified_by_id="patient_service"
        ),
        correlation_id="corr-7",
    )

    assert seen == [1]


def test_delete_ref_patient_logs_after_commit(mock_log_crud_action, bypass_idempotency):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _ref_patient()
    seen = _commits_seen_at_log(mock_log_crud_action, db)

    ref_patient_crud.delete_ref_patient(
        db=db,
        patient_id="1",
        patient_delete=RefPatientDelete(modified_date=datetime(2024, 3, 1), modified_by_id="patient_service"),
        correlation_id="corr-8",
    )

    assert seen == [1]

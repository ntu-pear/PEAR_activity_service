import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from app.crud.adhoc_crud import (
    create_adhoc,
    get_adhoc_by_id,
    get_adhocs,
    update_adhoc,
    delete_adhoc,
)
from app.models.adhoc_model import Adhoc as AdhocModel
from app.schemas.adhoc_schema import AdhocCreate, AdhocUpdate

@pytest.fixture
def valid_adhoc_data():
    """Returns a dict of minimal valid data for AdhocCreate."""
    now = datetime.now() + timedelta(hours=1)
    return {
        "old_centre_activity_id": 1,
        "new_centre_activity_id": 2,
        "patient_id": 1,
        "status": "PENDING",
        "start_date": now,
        "end_date": now + timedelta(hours=1),
        "created_by_id": "user1",
    }

### Schema validation ###
def test_schema_rejects_same_activity_ids(valid_adhoc_data):
    valid_adhoc_data["new_centre_activity_id"] = valid_adhoc_data["old_centre_activity_id"]
    with pytest.raises(ValidationError):
        AdhocCreate(**valid_adhoc_data)

def test_schema_rejects_past_start_date(valid_adhoc_data):
    valid_adhoc_data["start_date"] = datetime.now() - timedelta(days=1)
    with pytest.raises(ValidationError):
        AdhocCreate(**valid_adhoc_data)

def test_schema_rejects_overlong_span(valid_adhoc_data):
    valid_adhoc_data["end_date"] = valid_adhoc_data["start_date"] + timedelta(days=8)
    with pytest.raises(ValidationError):
        AdhocCreate(**valid_adhoc_data)

def test_schema_accepts_good_data(valid_adhoc_data):
    # should not raise
    AdhocCreate(**valid_adhoc_data)

# def test_create_adhoc_success(get_db_session_mock, valid_adhoc_data, mock_supervisor_user, monkeypatch):
#     db: Session = get_db_session_mock
#     # stub centre-activity lookup
#     monkeypatch.setattr(
#         "app.crud.adhoc_crud.get_centre_activity_by_id",
#         lambda db, centre_activity_id: MagicMock(id=centre_activity_id)
#     )
#     # disable logging side‐effects
#     monkeypatch.setattr("app.crud.adhoc_crud.log_crud_action", lambda *args, **kwargs: None)
#     # stub patient lookup to succeed
#     monkeypatch.setattr(
#         "app.services.patient_service.get_patient_by_id",
#         lambda require_auth, bearer_token, patient_id: None
#     )
#     adhoc_obj = AdhocCreate(**valid_adhoc_data)
#     result = create_adhoc(db, adhoc_obj, mock_supervisor_user)

#     assert isinstance(result, AdhocModel)
#     assert result.old_centre_activity_id == valid_adhoc_data["old_centre_activity_id"]
#     assert result.new_centre_activity_id == valid_adhoc_data["new_centre_activity_id"]
#     assert result.created_by_id == valid_adhoc_data["created_by_id"]

#     db.add.assert_called_once_with(result)
#     db.commit.assert_called_once()
#     db.refresh.assert_called_once_with(result)

def test_create_adhoc_old_not_found(get_db_session_mock, valid_adhoc_data, mock_supervisor_user, monkeypatch):
    db: Session = get_db_session_mock
    # old not found
    monkeypatch.setattr(
        "app.crud.adhoc_crud.get_centre_activity_by_id",
        lambda db, centre_activity_id: None
    )
    adhoc_obj = AdhocCreate(**valid_adhoc_data)
    with pytest.raises(HTTPException) as exc:
        create_adhoc(db, adhoc_obj, mock_supervisor_user)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Old centre activity not found" in exc.value.detail

def test_get_adhoc_by_id_success(get_db_session_mock):
    db = get_db_session_mock
    sample = AdhocModel(id=5)
    # chain .query().filter().first()
    db.query.return_value.filter.return_value.first.return_value = sample
    result = get_adhoc_by_id(db, adhoc_id=5, include_deleted=False)
    assert result is sample

def test_get_adhoc_by_id_not_found(get_db_session_mock):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        get_adhoc_by_id(db, adhoc_id=10, include_deleted=False)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_adhocs_success(get_db_session_mock):
    db = get_db_session_mock
    items = [AdhocModel(id=1), AdhocModel(id=2)]
    chain = db.query.return_value
    chain.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = items
    result = get_adhocs(db, include_deleted=False, skip=0, limit=10)
    assert result == items

def test_get_adhocs_no_results(get_db_session_mock):
    db = get_db_session_mock
    chain = db.query.return_value
    chain.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
    with pytest.raises(HTTPException) as exc:
        get_adhocs(db, include_deleted=False, skip=0, limit=10)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

@pytest.fixture
def existing_adhoc_instance():
    return AdhocModel(id=1, old_centre_activity_id=1, new_centre_activity_id=2,
                      patient_id=1, status="PENDING",
                      start_date=datetime.now() + timedelta(hours=1),
                      end_date=datetime.now() + timedelta(hours=2),
                      is_deleted=False,
                      created_by_id="user1",
                      created_date=datetime.now())

# def test_update_adhoc_success(get_db_session_mock, existing_adhoc_instance, valid_adhoc_data, mock_supervisor_user, monkeypatch):
#     db = get_db_session_mock
#     # stub query to return our existing instance
#     db.query.return_value.filter.return_value.first.return_value = existing_adhoc_instance
#     # stub centre-activity lookup
#     monkeypatch.setattr("app.crud.adhoc_crud.get_centre_activity_by_id", lambda db, centre_activity_id: MagicMock(id=centre_activity_id))
#     # disable logging side‐effects
#     monkeypatch.setattr("app.crud.adhoc_crud.log_crud_action", lambda *args, **kwargs: None)
#     # stub patient lookup to succeed
#     monkeypatch.setattr(
#         "app.services.patient_service.get_patient_by_id",
#         lambda require_auth, bearer_token, patient_id: None
#     )

#     upd_data = valid_adhoc_data.copy()
#     upd_data.update({
#         "id": existing_adhoc_instance.id,
#         "status": "APPROVED",
#         "modified_by_id": "user2",
#         "modified_date": datetime.now(),
#     })
#     adhoc_upd = AdhocUpdate(**upd_data)

#     result = update_adhoc(db, adhoc_upd, mock_supervisor_user)
#     assert result.status == "APPROVED"
#     assert result.modified_by_id == "user2"
#     db.commit.assert_called_once()
#     db.refresh.assert_called_once_with(existing_adhoc_instance)

def test_update_adhoc_not_found(get_db_session_mock, valid_adhoc_data, mock_supervisor_user):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.first.return_value = None
    upd = AdhocUpdate(id=999, **valid_adhoc_data, modified_by_id="x", modified_date=None)
    with pytest.raises(HTTPException) as exc:
        update_adhoc(db, upd, mock_supervisor_user)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_delete_adhoc_success(get_db_session_mock, existing_adhoc_instance, mock_supervisor_user, monkeypatch):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.first.return_value = existing_adhoc_instance
    monkeypatch.setattr("app.crud.adhoc_crud.log_crud_action", lambda *args, **kwargs: None)

    result = delete_adhoc(db, existing_adhoc_instance.id, mock_supervisor_user)
    assert result.is_deleted is True
    db.commit.assert_called_once()

def test_delete_adhoc_not_found(get_db_session_mock, mock_supervisor_user):
    db = get_db_session_mock
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        delete_adhoc(db, adhoc_id=123, current_user_info=mock_supervisor_user)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
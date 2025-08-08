import pytest
from datetime import date, datetime
from fastapi import HTTPException, status
from unittest import mock

from app.crud.centre_activity_exclusion_crud import (
    get_centre_activity_exclusion_by_id,
    get_centre_activity_exclusions,
    create_centre_activity_exclusion,
    update_centre_activity_exclusion,
    delete_centre_activity_exclusion,
)
from app.models.centre_activity_exclusion_model import CentreActivityExclusion as CentreActivityExclusionModel
from app.schemas.centre_activity_exclusion_schema import (
    CentreActivityExclusionCreate,
    CentreActivityExclusionUpdate,
)
from app.crud.centre_activity_exclusion_crud import model_to_dict, serialize_data

@pytest.fixture
def valid_exclusion_data():
    today = date.today()
    return {
        "centre_activity_id": 1,
        "patient_id": 2,
        "exclusion_remarks": "Test exclusion",
        "start_date": today,
        "end_date": today,
    }

@pytest.fixture
def existing_exclusion_instance(valid_exclusion_data):
    data = valid_exclusion_data.copy()
    return CentreActivityExclusionModel(
        id=1,
        centre_activity_id=data["centre_activity_id"],
        patient_id=data["patient_id"],
        is_deleted=False,
        exclusion_remarks=data["exclusion_remarks"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        created_date=datetime.utcnow(),
        modified_date=datetime.utcnow(),
        created_by_id="user1",
        modified_by_id="user1",
    )

def test_get_exclusion_by_id_success(get_db_session_mock, existing_exclusion_instance):
    db = get_db_session_mock
    db.query.return_value\
      .filter.return_value\
      .filter.return_value\
      .first.return_value = existing_exclusion_instance

    result = get_centre_activity_exclusion_by_id(db, exclusion_id=1)
    assert result is existing_exclusion_instance

def test_get_exclusion_by_id_not_found(get_db_session_mock):
    db = get_db_session_mock
    db.query.return_value\
      .filter.return_value\
      .filter.return_value\
      .first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_centre_activity_exclusion_by_id(db, exclusion_id=999)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_exclusions_success(get_db_session_mock):
    exclusions = [mock.MagicMock(), mock.MagicMock()]
    chain = (
        get_db_session_mock.query.return_value
        .filter.return_value
        .order_by.return_value
        .offset.return_value
        .limit.return_value
    )
    chain.all.return_value = exclusions

    result = get_centre_activity_exclusions(get_db_session_mock, include_deleted=False, skip=5, limit=2)
    assert result == exclusions

def test_get_exclusions_include_deleted(get_db_session_mock):
    exclusions = [mock.MagicMock()]
    chain = (
        get_db_session_mock.query.return_value
        .order_by.return_value
        .offset.return_value
        .limit.return_value
    )
    chain.all.return_value = exclusions

    result = get_centre_activity_exclusions(get_db_session_mock, include_deleted=True, skip=0, limit=10)
    assert result == exclusions

@mock.patch("app.crud.centre_activity_exclusion_crud.models.CentreActivityExclusion")
def test_create_exclusion_success(
    mock_exclusion_cls,
    get_db_session_mock,
    valid_exclusion_data,
    mock_supervisor_user,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.get_centre_activity_by_id",
        lambda db, centre_activity_id: True
    )
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.get_patient_by_id",
        lambda *args, **kwargs: True
    )
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.log_crud_action",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr("app.crud.centre_activity_exclusion_crud.model_to_dict", lambda obj: {"id": 1})
    monkeypatch.setattr("app.crud.centre_activity_exclusion_crud.serialize_data", lambda d: d)

    fake_obj = mock_exclusion_cls.return_value
    payload = CentreActivityExclusionCreate(**valid_exclusion_data)
    result = create_centre_activity_exclusion(get_db_session_mock, payload, mock_supervisor_user)

    assert result is fake_obj
    get_db_session_mock.add.assert_called_once_with(fake_obj)
    get_db_session_mock.commit.assert_called_once()
    get_db_session_mock.refresh.assert_called_once_with(fake_obj)

def test_create_exclusion_centre_activity_not_found(
    get_db_session_mock, valid_exclusion_data, mock_supervisor_user, monkeypatch
):
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.get_centre_activity_by_id",
        lambda db, centre_activity_id: False
    )

    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_exclusion(
            get_db_session_mock,
            CentreActivityExclusionCreate(**valid_exclusion_data),
            mock_supervisor_user,
        )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

def test_create_exclusion_invalid_patient(
    get_db_session_mock, valid_exclusion_data, mock_supervisor_user, monkeypatch
):
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.get_centre_activity_by_id",
        lambda db, centre_activity_id: True
    )
    def fake_patient(*args, **kwargs):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    monkeypatch.setattr("app.crud.centre_activity_exclusion_crud.get_patient_by_id", fake_patient)

    with pytest.raises(HTTPException) as exc_info:
        create_centre_activity_exclusion(
            get_db_session_mock,
            CentreActivityExclusionCreate(**valid_exclusion_data),
            mock_supervisor_user,
        )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

@mock.patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusion_by_id")
def test_update_exclusion_success(
    mock_get,
    get_db_session_mock,
    existing_exclusion_instance,
    mock_supervisor_user,
    monkeypatch,
    valid_exclusion_data,
):
    mock_get.return_value = existing_exclusion_instance
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.get_centre_activity_by_id",
        lambda db, centre_activity_id: True
    )
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.get_patient_by_id",
        lambda *args, **kwargs: True
    )
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.log_crud_action",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr(model_to_dict.__module__ + ".model_to_dict", lambda obj: {"dummy": 1})
    monkeypatch.setattr(serialize_data.__module__ + ".serialize_data", lambda d: d)

    update_payload = {
        **valid_exclusion_data,
        "id": existing_exclusion_instance.id,
        "centre_activity_id": 99,
        "patient_id": 100,
        "modified_by_id": "user2",
    }
    payload = CentreActivityExclusionUpdate(**update_payload)
    result = update_centre_activity_exclusion(get_db_session_mock, payload, mock_supervisor_user)

    assert result is existing_exclusion_instance
    get_db_session_mock.commit.assert_called_once()
    get_db_session_mock.refresh.assert_called_once_with(existing_exclusion_instance)

@mock.patch("app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusion_by_id")
def test_update_exclusion_centre_activity_not_found(
    mock_get,
    get_db_session_mock,
    existing_exclusion_instance,
    mock_supervisor_user,
    monkeypatch,
    valid_exclusion_data,
):
    mock_get.return_value = existing_exclusion_instance
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.get_centre_activity_by_id",
        lambda db, centre_activity_id: False
    )

    with pytest.raises(HTTPException) as exc_info:
        update_centre_activity_exclusion(
            get_db_session_mock,
            CentreActivityExclusionUpdate(
                **{
                    **valid_exclusion_data,
                    "id": existing_exclusion_instance.id,
                    "modified_by_id": "user2",
                }
            ),
            mock_supervisor_user,
        )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

def test_delete_exclusion_success(
    get_db_session_mock, existing_exclusion_instance, mock_supervisor_user, monkeypatch
):
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusion_by_id",
        lambda db, exclusion_id: existing_exclusion_instance
    )
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.log_crud_action",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr(model_to_dict.__module__ + ".model_to_dict", lambda obj: {"dummy": 1})
    monkeypatch.setattr(serialize_data.__module__ + ".serialize_data", lambda d: d)

    result = delete_centre_activity_exclusion(get_db_session_mock, existing_exclusion_instance.id, mock_supervisor_user)
    assert result.is_deleted is True
    get_db_session_mock.commit.assert_called_once()

def test_delete_exclusion_not_found(get_db_session_mock, mock_supervisor_user, monkeypatch):
    monkeypatch.setattr(
        "app.crud.centre_activity_exclusion_crud.get_centre_activity_exclusion_by_id",
        lambda db, exclusion_id: (_ for _ in ()).throw(HTTPException(status_code=status.HTTP_404_NOT_FOUND))
    )

    with pytest.raises(HTTPException) as exc_info:
        delete_centre_activity_exclusion(get_db_session_mock, exclusion_id=123, current_user_info=mock_supervisor_user)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
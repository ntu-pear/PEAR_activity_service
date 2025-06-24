import pytest
from unittest.mock import MagicMock, patch
import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import ValidationError
import conftest
from app.models.centre_activity_model import CentreActivity as CentreActivityModel
from app.schemas.centre_activity_schema import CentreActivityCreate, CentreActivityUpdate, CentreActivityResponse
from app.crud.centre_activity_crud import (
    create_centre_activity,
    get_centre_activity_by_id,
    get_centre_activities,
    update_centre_activity,
    delete_centre_activity,
)

@pytest.fixture
def create_centre_activity_schema(base_centre_activity_data):
    return CentreActivityCreate(**base_centre_activity_data)

@pytest.fixture
def update_centre_activity_schema():
    return CentreActivityUpdate(
        id=1,
        activity_id=1,
        is_compulsory=True,
        modified_by_id=1
    )
#==========


@pytest.mark.parametrize(
    "override_fields, expected_error",
    [
        # Invalid: individual but min_people_req != 1
        ({"is_group": False, "min_people_req": 2}, "Individual activities must have a minimum of 1 person"),

        # Invalid: group but min_people_req < 2
        ({"is_group": True, "min_people_req": 1}, "Group activities must have a minimum of 2"),

        # Invalid: fixed but min != max
        ({"is_fixed": True, "min_duration": 30, "max_duration": 60}, "Fixed duration activities must have the same"),

        # Invalid: flexible but min > max
        ({"is_fixed": False, "min_duration": 60, "max_duration": 30}, "Flexible activities, ensure minimum"),

        # Invalid: duration not in (30, 60)
        ({"min_duration": 45, "max_duration": 45}, "Duration must be either 30 or 60"),
    ]
)
def test_centre_activity_schema_validation_fails(base_centre_activity_data, override_fields, expected_error):
    """Tests validation logic inside @model_validator"""

    data = {**base_centre_activity_data, **override_fields}
    
    with pytest.raises(ValidationError) as exc:
        CentreActivityCreate(**data)

    assert expected_error in str(exc.value)

@patch("app.crud.centre_activity_crud.get_activity_by_id")
def test_create_centre_activity_success(mock_get_activity, get_db_session_mock, mock_current_user, 
                                     create_centre_activity_schema, existing_activity):
    '''Creates when activity exists and no dulpicate centre activity exists.'''

    mock_get_activity.return_value = existing_activity                                          # Valid Activity ID
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None     # No duplicate Centre Activity
    get_db_session_mock.refresh.return_value = existing_activity

    result = create_centre_activity(
        db=get_db_session_mock,
        centre_activity_data=create_centre_activity_schema,
        current_user_info=mock_current_user
    )

    assert result.modified_by_id == create_centre_activity_schema.created_by_id
    assert result.is_compulsory == create_centre_activity_schema.is_compulsory
    assert result.is_fixed == create_centre_activity_schema.is_fixed
    assert result.is_group == create_centre_activity_schema.is_group
    assert result.min_duration == create_centre_activity_schema.min_duration
    assert result.max_duration == create_centre_activity_schema.max_duration
    assert result.min_people_req == create_centre_activity_schema.min_people_req
    
    get_db_session_mock.add.assert_called_once()
    get_db_session_mock.commit.assert_called_once()

@patch("app.crud.centre_activity_crud.get_activity_by_id")
def test_create_centre_activity_activity_not_found_fail(mock_get_activity, get_db_session_mock, mock_current_user,
                                          create_centre_activity_schema):
    '''Fails to create when invalid Activity ID given'''

    mock_get_activity.return_value = None                                                       # Invalid Activity ID
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None     # No duplicate Centre Activity
    get_db_session_mock.refresh.return_value = None

    with pytest.raises(HTTPException) as exc:
        create_centre_activity(
            db=get_db_session_mock,
            centre_activity_data=create_centre_activity_schema,
            current_user_info=mock_current_user
        )
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Activity not found"

@patch("app.crud.centre_activity_crud.get_activity_by_id")
def test_create_centre_activity_duplicate_fail(mock_get_activity, get_db_session_mock, mock_current_user, 
                                     create_centre_activity_schema, existing_activity, existing_centre_activity):
    
    '''Fails to create when an identical record of Centre Activity already exists'''

    mock_get_activity.return_value = existing_activity                                                           # Valid Activity ID
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = existing_centre_activity  # Duplicate Centre Activity
    get_db_session_mock.refresh.return_value = existing_centre_activity

    with pytest.raises(HTTPException) as exc:
        create_centre_activity(
            db=get_db_session_mock,
            centre_activity_data=create_centre_activity_schema,
            current_user_info=mock_current_user
            )
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == "Centre Activity with these attributes already exists (including soft-deleted records)."



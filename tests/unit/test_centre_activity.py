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
def update_centre_activity_schema(base_centre_activity_data_list):
    return CentreActivityUpdate(**base_centre_activity_data_list[1])


#===== Validator tests =========
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

        # Invalid: start_date in the past
        ({"start_date": datetime.datetime.now().date() - datetime.timedelta(days=1)}, "Start date cannot be in the past"),

        # Invalid: end_date before start_date
        ({"end_date": datetime.datetime.now().date() - datetime.timedelta(days=1)}, "End date cannot be before start date"),
        
        # Invalid: end_date more than 1 year in the future
        ({"end_date": datetime.datetime.now().date() + datetime.timedelta(days=366)}, "End date cannot be more than 1 year in the future"),
    ]
)
@pytest.mark.parametrize("schema_class", [CentreActivityCreate, CentreActivityUpdate])
def test_centre_activity_schema_validation_fails(base_centre_activity_data, schema_class, override_fields, expected_error):
    """Tests validation logic inside @model_validator for both Create and Update schema"""

    data = {**base_centre_activity_data, **override_fields}
    
    with pytest.raises(ValidationError) as exc:
        schema_class(**data)

    assert expected_error in str(exc.value)

#======= CREATE tests ===========
@patch("app.crud.centre_activity_crud.get_activity_by_id")
def test_create_centre_activity_success(mock_get_activity, get_db_session_mock, mock_current_user, 
                                     create_centre_activity_schema, existing_activity):
    '''Creates when activity exists and no dulpicate centre activity exists.'''

    # Valid Activity ID
    mock_get_activity.return_value = existing_activity      
    # No duplicate Centre Activity                                    
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None     
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

    # Invalid Activity ID
    mock_get_activity.return_value = None
    # No duplicate Centre Activity                                                       
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = None     
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

    # Valid Activity ID
    mock_get_activity.return_value = existing_activity
    # Duplicate Centre Activity                                                           
    get_db_session_mock.query.return_value.filter_by.return_value.first.return_value = existing_centre_activity  
    get_db_session_mock.refresh.return_value = existing_centre_activity

    with pytest.raises(HTTPException) as exc:
        create_centre_activity(
            db=get_db_session_mock,
            centre_activity_data=create_centre_activity_schema,
            current_user_info=mock_current_user
            )
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == {
        'existing_id': '1', 
        'existing_is_deleted': False, 
        'message': 'Centre Activity with these attributes already exists (including soft-deleted records)'
        }

#===== GET tests ======
def test_get_centre_acitivity_by_id_success(get_db_session_mock, existing_centre_activity):
    '''Gets when record is found'''

    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity

    result = get_centre_activity_by_id(
        db=get_db_session_mock, 
        centre_activity_id=1
        )

    assert result.modified_by_id == existing_centre_activity.created_by_id
    assert result.is_compulsory == existing_centre_activity.is_compulsory
    assert result.is_fixed == existing_centre_activity.is_fixed
    assert result.is_group == existing_centre_activity.is_group
    assert result.min_duration == existing_centre_activity.min_duration
    assert result.max_duration == existing_centre_activity.max_duration
    assert result.min_people_req == existing_centre_activity.min_people_req

def test_get_centre_activity_by_id_fail(get_db_session_mock):
    '''Fails when record is not found'''

    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        get_centre_activity_by_id(
            db=get_db_session_mock,
            centre_activity_id=999
        )
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Centre Activity not found"

def test_get_centre_activities_success(get_db_session_mock, existing_centre_activities):
    '''Gets all Centre Activity records'''

    get_db_session_mock.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = existing_centre_activities

    print("Existing Centre Activities:", existing_centre_activities)
    result = get_centre_activities(db=get_db_session_mock)

    assert len(result) == 2

    # Assert the list
    for actual, expected in zip(result, existing_centre_activities):
        assert actual.id == expected.id
        assert actual.activity_id == expected.activity_id
        assert actual.is_compulsory == expected.is_compulsory
        assert actual.is_fixed == expected.is_fixed
        assert actual.is_group == expected.is_group
        assert actual.min_duration == expected.min_duration
        assert actual.max_duration == expected.max_duration
        assert actual.min_people_req == expected.min_people_req
        assert actual.created_by_id == expected.created_by_id
        assert actual.modified_by_id == expected.modified_by_id

#======= UPDATE tests =====
@patch("app.crud.centre_activity_crud.get_activity_by_id")
def test_update_centre_activity_success(mock_get_activity, get_db_session_mock, mock_current_user,
                                     update_centre_activity_schema, existing_activity,
                                     existing_centre_activity):
    """Updates Centre Activity if target to be updated exists and activity id provided exists"""

    # Valid Centre Activity
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity
    # Valid Activity    
    mock_get_activity.return_value = existing_activity
    # No duplicate Centre Activity                                                          
    get_db_session_mock.query.return_value.filter.return_value.filter_by.return_value.first.return_value = None     

    result = update_centre_activity(
        db=get_db_session_mock,
        centre_activity_data=update_centre_activity_schema,
        current_user_info=mock_current_user
    )
    
    # Fields that should not be updated
    assert result.id == existing_centre_activity.id                         # PK id should not be changed.
    assert result.created_date == existing_centre_activity.created_date     # Date of creation should not be changed
    
    # Fields that should be updated
    assert result.is_compulsory == update_centre_activity_schema.is_compulsory
    assert result.is_fixed == update_centre_activity_schema.is_fixed
    assert result.is_group == update_centre_activity_schema.is_group
    assert result.min_duration == update_centre_activity_schema.min_duration
    assert result.max_duration == update_centre_activity_schema.max_duration
    assert result.min_people_req == update_centre_activity_schema.min_people_req
    assert result.modified_by_id == update_centre_activity_schema.modified_by_id
    
    get_db_session_mock.commit.assert_called_once()

@patch("app.crud.centre_activity_crud.get_activity_by_id")
def test_update_centre_activity_not_found(mock_get_activity, get_db_session_mock, mock_current_user,
                                        update_centre_activity_schema, existing_activity):
    """Test update fails when centre activity doesn't exist"""

    # Centre Activity not found
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None  
    # Valid Activity  
    mock_get_activity.return_value = existing_activity
    
    with pytest.raises(HTTPException) as exc:
        update_centre_activity(
            db=get_db_session_mock,
            centre_activity_data=update_centre_activity_schema,
            current_user_info=mock_current_user
        )
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Centre Activity not found"

@patch("app.crud.centre_activity_crud.get_activity_by_id")
def test_update_centre_activity_invalid_activity(mock_get_activity, get_db_session_mock, mock_current_user,
                                        update_centre_activity_schema, existing_centre_activity):
    """Test update fails when activity doesn't exist"""

    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity    
    mock_get_activity.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        update_centre_activity(
            db=get_db_session_mock,
            centre_activity_data=update_centre_activity_schema,
            current_user_info=mock_current_user
        )
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Activity not found"

@patch("app.crud.centre_activity_crud.get_activity_by_id")
def test_update_centre_activity_duplicate_fail(mock_get_activity, get_db_session_mock, mock_current_user,
                                     update_centre_activity_schema, existing_activity,
                                     existing_centre_activity):
    """Test update fails when an identical record of Centre Activity already exists"""
    # Valid Centre Activity
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity        
    # Valid Activity
    mock_get_activity.return_value = existing_activity
    # Duplicate Centre Activity                                                          
    get_db_session_mock.query.return_value.filter.return_value.filter_by.return_value.first.return_value = existing_centre_activity     

    with pytest.raises(HTTPException) as exc:
        update_centre_activity(
            db=get_db_session_mock,
            centre_activity_data=update_centre_activity_schema,
            current_user_info=mock_current_user
        )
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == {
        'existing_id': str(existing_centre_activity.id), 
        'existing_is_deleted': existing_centre_activity.is_deleted, 
        'message': 'Centre Activity with these attributes already exists (including soft-deleted records)'
    }

#======= DELETE tests ==================
def test_delete_centre_activity_success(get_db_session_mock, mock_current_user,
                                existing_centre_activity):
    """Deletes when Centre Activity record exists and is_deleted is false"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = existing_centre_activity    # Centre Activity record exists

    result = delete_centre_activity(
        db=get_db_session_mock,
        centre_activity_id=existing_centre_activity.id,
        current_user_info=mock_current_user
    )
    
    assert result.id == existing_centre_activity.id
    assert result.is_deleted == True
    assert result.modified_by_id == mock_current_user.get("id")

def test_delete_centre_activity_not_found_fail(get_db_session_mock, mock_current_user,
                                existing_centre_activity):
    """Deletes when Centre Activity record exists and is_deleted is false"""
    get_db_session_mock.query.return_value.filter.return_value.first.return_value = None    # Centre Activity record not found (including is_deleted=True)

    with pytest.raises(HTTPException) as exc:
        delete_centre_activity(
            db=get_db_session_mock,
            centre_activity_id=existing_centre_activity.id,
            current_user_info=mock_current_user
        )
    
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Centre Activity not found (including soft-deleted records)"

    
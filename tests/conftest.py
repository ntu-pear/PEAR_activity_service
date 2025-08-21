import pytest
from unittest.mock import MagicMock, create_autospec
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.activity_model import Activity
from app.models.centre_activity_model import CentreActivity
from app.models.care_centre_model import CareCentre
from app.auth.jwt_utils import JWTPayload


@pytest.fixture()
def get_db_session_mock():
    """Fixture to create a mock database session."""
    return create_autospec(Session, instance=True)

@pytest.fixture
def mock_supervisor_user():
    return {
        "id": "2",
        "fullName": "Test User",
        "email": "test@test.com",
        "roleName": "SUPERVISOR",
    }

@pytest.fixture
def mock_caregiver_user():
    return {
        "id": "3",
        "fullName": "Test Caregiver",
        "email": "caregiver@test.com",
        "role_name": "CAREGIVER",
        "bearer_token": "test-bearer-token",
    }

@pytest.fixture
def mock_supervisor_jwt():
     return JWTPayload(
        userId="2",
        fullName="Test User",
        email="test@test.com",
        roleName="SUPERVISOR",
        sessionId="abc321"
    )

@pytest.fixture
def mock_caregiver_jwt():
    return JWTPayload(
        userId="3",
        fullName="Test Caregiver",
        email="caregiver@test.com",
        roleName="CAREGIVER",
        sessionId="abc456"
    )

@pytest.fixture
def mock_admin_jwt():
    return JWTPayload(
        userId="123",
        fullName="John Doe",
        email="test@test.com",
        roleName="ADMIN",
        sessionId="abc123"
    )

@pytest.fixture
def mock_doctor_jwt():
    return JWTPayload(
        userId="456",
        fullName="Jane Smith",
        email="doctor@test.com",
        roleName="DOCTOR",
        sessionId="def456"
    )

@pytest.fixture
def mock_allocation_response():
    """Mock response for patient service calls"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "patientId": 1,
        "caregiverId": "3",
        "supervisorId": "2"
    }
    return mock_response

@pytest.fixture
def mock_patient_service_response():
    """Mock response for patient service calls"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "patientId": 1,
        "address": "Singapore",
        "gender": "F",
        "patientName": "Test Patient"
    }
    return mock_response
# ====== Care Centre Fixtures ======
@pytest.fixture
def base_care_centre_data_list():
    '''Base data for Care Centre'''
    return [
        {
            "id": 1,
            "is_deleted": False,
            "name": "Test Care Centre",
            "country_code": "SGP",
            "address": "123 Test St",
            "postal_code": "123456",
            "contact_no": "6512345678",
            "email": "test@gmail.com",
            "no_of_devices_avail": 10,
            "working_hours": {
                "monday": {"open": "09:00", "close": "17:00"},
                "tuesday": {"open": "09:00", "close": "17:00"},
                "wednesday": {"open": "09:00", "close": "17:00"},
                "thursday": {"open": "09:00", "close": "17:00"},
                "friday": {"open": "09:00", "close": "17:00"},
                "saturday": {"open": None, "close": None},
                "sunday": {"open": None, "close": None},
            },
            "remarks": "Test remarks",
            "created_by_id": "1",
            "created_date": datetime.now(),
            "modified_by_id": "",
            "modified_date": datetime.now(),
        },
        {   # For update test
            "id": 1,
            "is_deleted": True,
            "name": "Test Care Centre",
            "country_code": "SGP",
            "address": "123 Test St",
            "postal_code": "123456",
            "contact_no": "6512345678",
            "email": "UPDATETEST@gmail.com",
            "no_of_devices_avail": 5,
            "working_hours": {
                "monday": {"open": "09:00", "close": "17:00"},
                "tuesday": {"open": "09:00", "close": "17:00"},
                "wednesday": {"open": "09:00", "close": "17:00"},
                "thursday": {"open": "09:00", "close": "17:00"},
                "friday": {"open": "09:00", "close": "17:00"},
                "saturday": {"open": "09:00", "close": "14:00"},
                "sunday": {"open": None, "close": None},
            },
            "remarks": "Test remarks",
            "created_by_id": "1",
            "created_date": datetime.now(),
            "modified_by_id": "1",
            "modified_date": datetime.now(),
        },
    ]

@pytest.fixture
def base_care_centre_data(base_care_centre_data_list):
    return base_care_centre_data_list[0]

@pytest.fixture
def existing_care_centre(base_care_centre_data):
    """A CareCentre instance for mocking DB data"""
    return CareCentre(**base_care_centre_data)

@pytest.fixture
def existing_care_centres(base_care_centre_data_list):
    """A list of CareCentre instance for mocking DB data"""
    return [CareCentre(**data) for data in base_care_centre_data_list]

@pytest.fixture
def soft_deleted_care_centre(base_care_centre_data):
    """Soft-deleted CareCentre instance"""
    data = base_care_centre_data.copy()
    data.update({
        "id": 1,
        "is_deleted": True,
        "modified_date": datetime.now()
    })
    return CareCentre(**data)


#====== Activity Fixtures ======

@pytest.fixture
def base_activity_data():
    """Base data for Activity"""
    return {
        "id": 1,
        "is_deleted": False,
        "title": "Old Title",
        "description": "Old Description"
    }

@pytest.fixture
def existing_activity(base_activity_data):
    """An Activity instance for retrieval/update/delete."""
    return Activity(**base_activity_data)


# ===Centre Activity Fixtures ===
@pytest.fixture
def base_centre_activity_data_list():
    """Base data for Centre Activity"""
    return [
        {
            "id": 1,
            "activity_id": 1,
            "is_deleted": False,
            "is_compulsory": True,
            "is_fixed": False,
            "is_group": False,
            "start_date": datetime.now().date(),
            "end_date": None,
            "min_duration": 30,
            "max_duration": 60,
            "min_people_req": 1,
            "created_by_id": "1",
            "modified_by_id": "1",
            "created_date": datetime.now(),
            "modified_date": datetime.now(),
        },
        {   # For update test
            "id": 1,
            "activity_id": 2,
            "is_deleted": False,
            "is_compulsory": True,
            "is_fixed": True,
            "is_group": True,
            "start_date": datetime.now().date(),
            "end_date": None,
            "min_duration": 60,
            "max_duration": 60,
            "min_people_req": 4,
            "created_by_id": "2",
            "modified_by_id": "2",
            "created_date": datetime.now(),
            "modified_date": datetime.now(),
        },
    ]

@pytest.fixture
def base_centre_activity_data(base_centre_activity_data_list):
    return base_centre_activity_data_list[0]

@pytest.fixture
def existing_centre_activity(base_centre_activity_data):
    """A CentreActivity instance for mocking DB data"""
    return CentreActivity(**base_centre_activity_data)

@pytest.fixture
def existing_centre_activities(base_centre_activity_data_list):
    """A list of CentreActivity instance for mocking DB data"""
    return [CentreActivity(**data) for data in base_centre_activity_data_list]

@pytest.fixture
def soft_deleted_centre_activity(base_centre_activity_data):
    """Soft-deleted CentreActivity instance"""
    data = base_centre_activity_data.copy()
    data.update({
        "id": 1,  
        "is_deleted": True,
        "modified_date": datetime.now()
    })
    return CentreActivity(**data)

# === Centre Activity Preference Fixtures ===
@pytest.fixture
def base_centre_activity_preference_data_list():
    """Base data for Centre Activity Preference"""
    return [
        {
            "id": 1,
            "centre_activity_id": 1,
            "patient_id": 1,
            "is_like": True,
            "is_deleted": False,
            "created_date": datetime.now(),
            "modified_date": datetime.now(),
            "created_by_id": "3",
            "modified_by_id": "3",
        },
        {   # For update test - use id for schema (aliased to centre_activity_preference_id)
            "id": 1,
            "centre_activity_id": 2,
            "patient_id": 1,
            "is_like": False,
            "is_deleted": False,
            "created_date": datetime.now(),
            "modified_date": datetime.now(),
            "created_by_id": "3",
            "modified_by_id": "3",
        },
    ]

@pytest.fixture
def base_centre_activity_preference_data(base_centre_activity_preference_data_list):
    return base_centre_activity_preference_data_list[0]

@pytest.fixture
def existing_centre_activity_preference(base_centre_activity_preference_data):
    """A CentreActivityPreference instance for mocking DB data"""
    from app.models.centre_activity_preference_model import CentreActivityPreference
    # Convert back to model field names
    model_data = base_centre_activity_preference_data.copy()
    # Remove any schema-specific fields that don't exist in the model
    if "centre_activity_preference_id" in model_data:
        del model_data["centre_activity_preference_id"]
    return CentreActivityPreference(**model_data)

@pytest.fixture
def existing_centre_activity_preferences(base_centre_activity_preference_data_list):
    """A list of CentreActivityPreference instance for mocking DB data"""
    from app.models.centre_activity_preference_model import CentreActivityPreference
    # Create model data with proper field names
    model_data_1 = base_centre_activity_preference_data_list[0].copy()
    model_data_2 = {
        "id": 2,
        "centre_activity_id": 2,
        "patient_id": 1,
        "is_like": False,
        "is_deleted": False,
        "created_date": datetime.now(),
        "modified_date": datetime.now(),
        "created_by_id": "3",
        "modified_by_id": "3",
    }
    return [CentreActivityPreference(**model_data_1), CentreActivityPreference(**model_data_2)]

@pytest.fixture
def soft_deleted_centre_activity_preference(base_centre_activity_preference_data):
    """Soft-deleted CentreActivityPreference instance"""
    from app.models.centre_activity_preference_model import CentreActivityPreference
    data = base_centre_activity_preference_data.copy()
    data.update({
        "id": 1,
        "is_deleted": True,
        "modified_date": datetime.now()
    })
    return CentreActivityPreference(**data)


# ====== Centre Activity Recommendation Fixtures ======
@pytest.fixture
def mock_doctor_allocation_response():
    """Mock response for patient allocation with doctor"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "patientId": 1,
        "caregiverId": "3",
        "supervisorId": "2",
        "doctorId": "456"  # matches mock_doctor_jwt userId
    }
    return mock_response

@pytest.fixture
def mock_doctor_user():
    return {
        "id": "456",
        "fullname": "Dr. Jane Smith",
        "role_name": "DOCTOR",
        "bearer_token": "test-doctor-token",
    }

@pytest.fixture
def base_centre_activity_recommendation_data_list():
    """Base data for Centre Activity Recommendation"""
    return [
        {
            "id": 1,
            "centre_activity_id": 1,
            "patient_id": 1,
            "doctor_id": 456,
            "doctor_remarks": "Recommended for cognitive improvement",
            "is_deleted": False,
            "created_date": datetime.now(),
            "modified_date": datetime.now(),
            "created_by_id": "456",
            "modified_by_id": "456",
        },
        {   # For update test - use id for schema (aliased to centre_activity_recommendation_id)
            "id": 1,
            "centre_activity_id": 2,
            "patient_id": 1,
            "doctor_id": 456,
            "doctor_remarks": "Good for physical therapy",
            "is_deleted": False,
            "created_date": datetime.now(),
            "modified_date": datetime.now(),
            "created_by_id": "456",
            "modified_by_id": "456",
        },
    ]

@pytest.fixture
def base_centre_activity_recommendation_data(base_centre_activity_recommendation_data_list):
    return base_centre_activity_recommendation_data_list[0]

@pytest.fixture
def existing_centre_activity_recommendation(base_centre_activity_recommendation_data):
    """A CentreActivityRecommendation instance for mocking DB data"""
    from app.models.centre_activity_recommendation_model import CentreActivityRecommendation
    # Convert back to model field names
    model_data = base_centre_activity_recommendation_data.copy()
    # Remove any schema-specific fields that don't exist in the model
    if "centre_activity_recommendation_id" in model_data:
        del model_data["centre_activity_recommendation_id"]
    return CentreActivityRecommendation(**model_data)

@pytest.fixture
def existing_centre_activity_recommendations(base_centre_activity_recommendation_data_list):
    """A list of CentreActivityRecommendation instance for mocking DB data"""
    from app.models.centre_activity_recommendation_model import CentreActivityRecommendation
    # Create model data with proper field names
    model_data_1 = base_centre_activity_recommendation_data_list[0].copy()
    model_data_2 = {
        "id": 2,
        "centre_activity_id": 2,
        "patient_id": 1,
        "doctor_id": 456,
        "doctor_remarks": "Recommended for social interaction",
        "is_deleted": False,
        "created_date": datetime.now(),
        "modified_date": datetime.now(),
        "created_by_id": "456",
        "modified_by_id": "456",
    }
    return [CentreActivityRecommendation(**model_data_1), CentreActivityRecommendation(**model_data_2)]

@pytest.fixture
def soft_deleted_centre_activity_recommendation(base_centre_activity_recommendation_data):
    """Soft-deleted CentreActivityRecommendation instance"""
    from app.models.centre_activity_recommendation_model import CentreActivityRecommendation
    data = base_centre_activity_recommendation_data.copy()
    data.update({
        "id": 1,
        "is_deleted": True,
        "modified_date": datetime.now()
    })
    return CentreActivityRecommendation(**data)


# ====== Centre Activity Availability Fixtures ======
@pytest.fixture
def base_centre_activity_availability_data_list():
    """Base data for Centre Activity Availability"""
    today = datetime.now()

    return [
        {
            "centre_activity_id": 1,
            "start_time": datetime.combine(today, datetime.strptime("09:00:00", "%H:%M:%S").time()),
            "end_time": datetime.combine(today, datetime.strptime("09:30:00", "%H:%M:%S").time()),
            "id": 1,
            "is_deleted": False,
            "created_date": datetime.now(),
            "modified_date": None,
            "created_by_id": "Test User",
            "modified_by_id": None
        },
        {
            "centre_activity_id": 1,
            "start_time": datetime.combine(today, datetime.strptime("09:30:00", "%H:%M:%S").time()),
            "end_time": datetime.combine(today, datetime.strptime("10:00:00", "%H:%M:%S").time()),
            "id": 2,
            "is_deleted": False,
            "created_date": datetime.now(),
            "modified_date": None,
            "created_by_id": "Test User",
            "modified_by_id": None
        }
    ]

@pytest.fixture
def base_centre_activity_availability_data(base_centre_activity_availability_data_list):
    return base_centre_activity_availability_data_list[0]

@pytest.fixture
def existing_centre_activity_availability(base_centre_activity_availability_data):
    from app.models.centre_activity_availability_model import CentreActivityAvailability
    return CentreActivityAvailability(**base_centre_activity_availability_data[0])

@pytest.fixture
def existing_centre_activity_availabilities(base_centre_activity_availability_data_list):
    from app.models.centre_activity_availability_model import CentreActivityAvailability
    return [CentreActivityAvailability(**data) for data in base_centre_activity_availability_data_list]

@pytest.fixture
def soft_deleted_centre_activity_availability(base_centre_activity_availability_data):
    from app.models.centre_activity_availability_model import CentreActivityAvailability
    data = base_centre_activity_availability_data.copy()
    data.update({
        "id": 1,
        "is_deleted": True,
        "modified_date": datetime.now()
    })
    return CentreActivityAvailability(**data)

@pytest.fixture
def soft_deleted_centre_activity_availabilities(base_centre_activity_availability_data_list):
    from app.models.centre_activity_availability_model import CentreActivityAvailability
    data_list = base_centre_activity_availability_data_list.copy()
    data_list.update({
        "id": 1,
        "is_deleted": True,
        "modified_date": datetime.now()
    })
    return [CentreActivityAvailability(**data) for data in data_list]

@pytest.fixture
def update_centre_activity_availability_schema(base_centre_activity_availability_data_list):
    today = datetime.now()

    return {
        "centre_activity_id": 2,
        "start_time": datetime.combine(today, datetime.strptime("09:30:00", "%H:%M:%S").time()),
        "end_time": datetime.combine(today, datetime.strptime("10:00:00", "%H:%M:%S").time()),
        "id": 1,
        "is_deleted": False,
        "created_date": datetime.now(),
        "modified_date": datetime.now(),
        "created_by_id": "Test User",
        "modified_by_id": "Test User"
    }
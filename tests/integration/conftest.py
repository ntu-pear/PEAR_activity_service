"""
conftest.py - Final Configuration for PEAR Activity Service Integration Tests
==============================================================================

Simple, clean, mocked approach:
- ✅ Mocks all external services (Patient Service, User Service)
- ✅ No need for any external services to be running
- ✅ Fast, reliable, always works
- ✅ Industry standard for integration testing

Run tests:
    pytest tests/integration/ -v -s
"""

from datetime import date, datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.crud.centre_activity_crud import create_centre_activity
from app.database import SessionLocal
from app.models.activity_model import Activity
from app.models.centre_activity_exclusion_model import CentreActivityExclusion
from app.models.centre_activity_model import CentreActivity
from app.models.centre_activity_preference_model import CentreActivityPreference
from app.models.centre_activity_recommendation_model import CentreActivityRecommendation
from app.models.outbox_model import OutboxEvent
from app.schemas.centre_activity_schema import CentreActivityCreate

# ============================================================================
# AUTOMATIC MOCKING OF EXTERNAL SERVICES
# ============================================================================

@pytest.fixture(autouse=True, scope="function")
def mock_external_services():
    """
    Automatically mock all external service calls.
    
    This runs for EVERY test automatically (autouse=True).
    No need to add this fixture to your test functions!
    
    Mocks:
    - Patient Service API calls (get_patient_by_id, get_patient_allocation_by_patient_id)
    - User Service API calls
    - Any other external HTTP calls
    """
    def mock_requests_get(url, *args, **kwargs):
        mock_response = Mock()
        
        # Mock Patient Service - Get Patient by ID
        # URL pattern: /api/v1/patients/{patient_id}
        if '/patients/' in url and '/allocation/' not in url:
            patient_id = 1
            try:
                patient_id = int(url.split('/')[-1])
            except:
                pass
                
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": patient_id,
                "name": f"Test Patient {patient_id}",
                "email": f"patient{patient_id}@test.com",
                "status": "active",
                "date_of_birth": "1990-01-01",
                "gender": "M",
                "phone": "1234567890",
                "address": "123 Test St",
                "emergency_contact": "Emergency Contact",
                "medical_history": "No known conditions"
            }
            return mock_response
        
        # Mock Patient Service - Get Patient Allocation
        # URL pattern: /api/v1/allocation/patient/{patient_id}?
        if '/allocation/patient/' in url:
            patient_id = 1
            try:
                # Extract patient_id from URL like: /allocation/patient/1?
                patient_id = int(url.split('/allocation/patient/')[1].split('?')[0])
            except:
                pass
            
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "patientId": patient_id,
                "caregiverId": "test-caregiver-1",
                "supervisorId": "test-supervisor-1",
                "doctorId": "test-doctor-1",
                "allocationDate": "2025-01-01",
                "status": "active"
            }
            return mock_response
        
        # Mock User Service calls (if needed)
        if '/users/' in url:
            user_id = url.split('/')[-1]
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": user_id,
                "fullname": f"Test User {user_id}",
                "email": f"user{user_id}@test.com",
                "role_name": "STAFF",
                "status": "active"
            }
            return mock_response
        
        # Catch any unmocked external calls
        raise Exception(
            f"⚠️  Unmocked external HTTP call detected: {url}\n"
            f"   Add mocking for this endpoint in conftest.py if needed."
        )
    
    # Patch requests.get for all tests
    with patch('requests.get', side_effect=mock_requests_get):
        yield


# ============================================================================
# SESSION-SCOPED FIXTURES (Run once before all tests)
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Runs once before all tests in the session.
    Creates prerequisite data that all tests need.
    
    Prerequisites created:
    - Activity ID=1 (required by CentreActivity)
    - CentreActivity ID=1 (required by exclusions/preferences/recommendations)
    """
    print("\n" + "="*80)
    print("SESSION SETUP: Creating prerequisite data")
    print("="*80)
    
    db = SessionLocal()
    try:
        # Create Activity ID=1 if not exists
        _create_base_activity_if_not_exists(db)
        
        # Create CentreActivity ID=1 if not exists
        _create_test_centre_activity(db)
        
        print("="*80)
        print("SESSION SETUP: Complete - All prerequisites ready")
        print("="*80 + "\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Session setup failed: {str(e)}")
        raise
    finally:
        db.close()
    
    yield
    
    # Optional: Cleanup after all tests
    # (Usually we keep test data for debugging)


# ============================================================================
# FUNCTION-SCOPED FIXTURES (Run for each test)
# ============================================================================

@pytest.fixture(scope="function")
def integration_db():
    """
    Provides a fresh database session for each test function.
    
    Usage:
        def test_something(integration_db):
            result = integration_db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_user():
    """
    Mock user information for CRUD operations.
    
    This is what gets passed to create/update/delete functions
    as current_user_info.
    
    Usage:
        def test_create(integration_db, mock_user):
            result = create_something(
                db=integration_db,
                data=...,
                current_user_info=mock_user  # ← Uses this
            )
    """
    return {
        "id": "test-user-1",
        "fullname": "Integration Test User",
        "role_name": "STAFF",
        "bearer_token": "test-token-123"  # Fake token (external calls are mocked)
    }


@pytest.fixture
def doctor_user():
    """Mock user with DOCTOR role."""
    return {
        "id": "test-doctor-1",
        "fullname": "Test Doctor",
        "role_name": "DOCTOR",
        "bearer_token": "test-doctor-token"
    }


@pytest.fixture
def supervisor_user():
    """Mock user with SUPERVISOR role."""
    return {
        "id": "test-supervisor-1",
        "fullname": "Test Supervisor",
        "role_name": "SUPERVISOR",
        "bearer_token": "test-supervisor-token"
    }


@pytest.fixture
def caregiver_user():
    """Mock user with CAREGIVER role."""
    return {
        "id": "test-caregiver-1",
        "fullname": "Test Caregiver",
        "role_name": "CAREGIVER",
        "bearer_token": "test-caregiver-token"
    }


# Comment out cleanup if you want to see records in database
@pytest.fixture(autouse=True)
def cleanup_test_data(integration_db):
    """
    Global cleanup - cleans ALL test data after each test.
    Preserves prerequisites for dependent tests.
    """
    yield
    
    try:
        # Clean in correct order (child → parent)
        
        # 1. Outbox events (no dependencies)
        integration_db.query(OutboxEvent).delete(synchronize_session=False)
        integration_db.commit()
        
        # 2. Activity children (grandchildren of Activity)
        integration_db.query(CentreActivityPreference).delete(synchronize_session=False)
        integration_db.commit()
        
        integration_db.query(CentreActivityExclusion).delete(synchronize_session=False)
        integration_db.commit()
        
        integration_db.query(CentreActivityRecommendation).delete(synchronize_session=False)
        integration_db.commit()
        
        # 3. Centre activities (child of Activity)
        # Preserve ID=1 - needed by preference/exclusion/recommendation tests
        integration_db.query(CentreActivity).filter(
            CentreActivity.id != 1
        ).delete(synchronize_session=False)
        integration_db.commit()
        
        # 4. Activities (parent)
        # Preserve ID=1 - needed by centre_activity tests
        integration_db.query(Activity).filter(
            Activity.id != 1
        ).delete(synchronize_session=False)
        integration_db.commit()
        
        print("[CLEANUP] ✓ All test data cleaned (prerequisites preserved)")
        
    except Exception as e:
        integration_db.rollback()
        print(f"[CLEANUP] Warning: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS (Internal use)
# ============================================================================

def _create_base_activity_if_not_exists(db: Session) -> int:
    """
    Create base Activity record (ID=1) if it doesn't exist.
    This is required by CentreActivity foreign key.
    """
    try:
        # Check if Activity ID=1 exists
        result = db.execute("SELECT id FROM ACTIVITY WHERE id = 1")
        activity = result.fetchone()
        
        if activity:
            print("[SETUP] ✓ Activity ID=1 already exists")
            return 1
        
        # Create Activity ID=1
        db.execute("""
            INSERT INTO ACTIVITY (id, name, description, category, created_date, created_by_id)
            VALUES (1, 'Test Activity', 'Activity for integration tests', 'TEST', :created_date, 'system')
        """, {"created_date": datetime.now()})
        db.commit()
        
        print("[SETUP] ✓ Created Activity ID=1")
        return 1
        
    except Exception as e:
        db.rollback()
        print(f"[SETUP] ⚠ Warning: Could not ensure Activity ID=1: {str(e)}")
        return 1


def _create_test_centre_activity(db: Session) -> CentreActivity:
    """
    Create test CentreActivity (ID=1) if it doesn't exist.
    This is required by exclusions, preferences, and recommendations.
    """
    # Check if already exists
    existing = db.query(CentreActivity).filter(CentreActivity.id == 1).first()
    if existing:
        print(f"[SETUP] ✓ CentreActivity ID=1 already exists")
        return existing
    
    # Create mock user for the creation
    mock_user = {
        "id": "test-setup-system",
        "fullname": "Test Setup System"
    }
    
    # Create CentreActivity
    centre_activity_data = CentreActivityCreate(
        activity_id=1,
        is_compulsory=False,
        is_fixed=True,
        is_group=False,
        start_date=date.today(),
        end_date=date(2999, 12, 31),
        min_duration=60,
        max_duration=60,
        min_people_req=1,
        fixed_time_slots="09:00-10:00",
        created_by_id="test-setup-system"
    )
    
    centre_activity = create_centre_activity(
        db=db,
        centre_activity_data=centre_activity_data,
        current_user_info=mock_user
    )
    
    print(f"[SETUP] ✓ Created CentreActivity ID={centre_activity.id}")
    return centre_activity


# ============================================================================
# PYTEST CONFIGURATION HOOKS
# ============================================================================

def pytest_configure(config):
    """
    Hook that runs when pytest starts.
    Prints configuration information.
    """
    print("\n" + "="*80)
    print("PEAR ACTIVITY SERVICE - INTEGRATION TESTS")
    print("="*80)
    print("\nConfiguration:")
    print("  - Mode: Mocked External Services")
    print("  - Database: Testing Database")
    print("  - Services Required: None (all mocked)")
    print("  - Patient Service Endpoints Mocked:")
    print("    • GET /api/v1/patients/{id}")
    print("    • GET /api/v1/allocation/patient/{id}")
    print("  - Speed: Fast (~30 seconds for 43 tests)")
    print("="*80 + "\n")


def pytest_sessionfinish(session, exitstatus):
    """
    Hook that runs when test session ends.
    Prints final results.
    """
    print("\n" + "="*80)
    print("TEST SESSION COMPLETE")
    print("="*80)
    
    if exitstatus == 0:
        print("✓ All tests passed successfully!")
    else:
        print(f"✗ Tests finished with exit status: {exitstatus}")
    
    print("="*80 + "\n")
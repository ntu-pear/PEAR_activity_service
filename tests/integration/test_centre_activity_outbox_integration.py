"""
Integration tests for Centre Activity Service (Publisher) Outbox Pattern
Tests the flow: Centre Activity CRUD -> OUTBOX_EVENTS table creation

Run Pytest with command: 
1. Run everything: pytest tests/integration/test_centre_activity_outbox_integration.py -v -s
2. Run specific test class: pytest tests/integration/test_centre_activity_outbox_integration.py::TestCentreActivityCreateOutbox -v -s
3. Run specific test function: pytest tests/integration/test_centre_activity_outbox_integration.py::TestCentreActivityCreateOutbox::test_create_centre_activity_creates_outbox_event -v -s

"""

import json
from datetime import date, datetime

import pytest
from sqlalchemy.orm import Session

from app.crud.centre_activity_crud import (
    create_centre_activity,
    delete_centre_activity,
    get_centre_activity_by_id,
    update_centre_activity,
)
from app.database import SessionLocal
from app.models.centre_activity_model import CentreActivity
from app.models.outbox_model import OutboxEvent
from app.schemas.centre_activity_schema import (
    CentreActivityCreate,
    CentreActivityUpdate,
)


@pytest.fixture(scope="function")
def integration_db():
    """
    Each test gets a fresh DB session.
    NOTE: This is taken from database.py
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def mock_user():
    """
    Mock user info for CRUD operations
    """
    return {
        "id": "test-user-1",
        "fullname": "Integration Test User"
    }
    

# Uncomment this when you are testing to ensure clean state. 
# NOTE (IMPORTANT): This will delete ALL records in the tables after each test function, so make sure you point to the testing DB, and not PROD!

# @pytest.fixture(autouse=True)
# def cleanup_test_data(integration_db):
#     """
#     Cleanup fixture that runs after each test.
#     Deletes all test data created during the test.
#     """
#     # This runs BEFORE the test
#     yield
    
#     # This runs AFTER the test - cleanup
#     try:
#         # Delete all outbox events first
#         integration_db.query(OutboxEvent).delete()
#         integration_db.commit()
        
#         # Delete all centre activities
#         integration_db.query(CentreActivity).delete()
#         integration_db.commit()
        
#         print("\n[CLEANUP] Test data cleared successfully")
#     except Exception as e:
#         integration_db.rollback()
#         print(f"\n[CLEANUP] Warning: Failed to cleanup test data: {str(e)}")

class TestCentreActivityCreateOutbox:    
    def test_create_centre_activity_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: Centre Activity data
        WHEN: create_centre_activity is called
        THEN: CentreActivity and OutboxEvent are created atomically
        
        Goal: Check if the creation of centre activity also creates an outbox event. This function checks if the created records are the same
        
        """
        centre_activity_data = CentreActivityCreate(
            activity_id=1,
            is_compulsory=True,
            is_fixed=True,
            is_group=False,
            start_date=date.today(),
            end_date=date(2999, 12, 31),
            min_duration=60,
            max_duration=60,
            min_people_req=1,
            fixed_time_slots="09:00-10:00",
            created_by_id="test-user-1"
        )
        
        # Create centre activity
        centre_activity = create_centre_activity(
            db=integration_db,
            centre_activity_data=centre_activity_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Centre Activity ID: {centre_activity.id}")
        print(f"  Activity ID: {centre_activity.activity_id}")
        print(f"  Is Compulsory: {centre_activity.is_compulsory}")
        print(f"  Created By: {centre_activity.created_by_id}")
        
        # Assertions: Centre Activity created
        assert centre_activity.id is not None
        assert centre_activity.activity_id == 1
        assert centre_activity.is_compulsory == True
        assert centre_activity.is_fixed == True
        assert centre_activity.created_by_id == "test-user-1"
        assert centre_activity.is_deleted == False
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(centre_activity.id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.event_type == "CENTRE_ACTIVITY_CREATED"
        assert outbox_event.aggregate_id == str(centre_activity.id)
        assert outbox_event.routing_key == f"activity.centre_activity.created.{centre_activity.id}"
        
        print(f"DONE: Created Outbox Event ID: {outbox_event.id}")
        print(f"  Event Type: {outbox_event.event_type}")
        print(f"  Correlation ID: {outbox_event.correlation_id}")
        
        # Verify payload structure
        payload = outbox_event.get_payload()
        assert payload["event_type"] == "CENTRE_ACTIVITY_CREATED"
        assert payload["centre_activity_id"] == centre_activity.id
        assert payload["created_by"] == "test-user-1"
        assert "correlation_id" in payload
        assert "timestamp" in payload

class TestCentreActivityUpdateOutbox:    
    def test_update_centre_activity_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing centre activity
        WHEN: update_centre_activity is called with changes
        THEN: OutboxEvent records changes atomically
        
        Goal: This function checks if updating a centre activity creates an outbox event with the changes.
        """
        # Create initial centre activity
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
            created_by_id="test-user-1"
        )
        centre_activity = create_centre_activity(
            db=integration_db,
            centre_activity_data=centre_activity_data,
            current_user_info=mock_user
        )
        original_id = centre_activity.id
        
        print(f"\nDONE: Created Centre Activity ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Update centre activity
        update_data = CentreActivityUpdate(
            id=original_id,
            activity_id=1,
            is_compulsory=False,
            is_fixed=True,
            is_group=True,  # Changed from False to True
            start_date=date.today(),
            end_date=date(2999, 12, 31),
            min_duration=60,
            max_duration=60,
            min_people_req=2,  # Changed from 1 to 2 (required for group activities)
            fixed_time_slots="09:00-10:00",
            is_deleted=False,
            modified_by_id="test-user-1",
            modified_date=datetime.now()
        )
        updated_centre_activity = update_centre_activity(
            db=integration_db,
            centre_activity_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Centre Activity ID: {original_id}")
        
        # Assertions: Centre Activity updated
        assert updated_centre_activity.is_group == True
        assert updated_centre_activity.min_people_req == 2
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "CENTRE_ACTIVITY_UPDATED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.centre_activity.updated.{original_id}"
        
        print(f"DONE: Created UPDATE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload contains changes
        payload = outbox_event.get_payload()
        assert "changes" in payload
        assert "is_group" in payload["changes"]
        assert payload["changes"]["is_group"]["old"] == False
        assert payload["changes"]["is_group"]["new"] == True
        assert "min_people_req" in payload["changes"]
        assert payload["changes"]["min_people_req"]["old"] == 1
        assert payload["changes"]["min_people_req"]["new"] == 2
    
    def test_update_with_no_changes_does_not_create_outbox(self, integration_db, mock_user):
        """
        GIVEN: An existing centre activity
        WHEN: update_centre_activity is called with no actual changes
        THEN: No new OutboxEvent is created for CENTRE_ACTIVITY_UPDATED
        NOTE: This function will create one extra record in the CentreActivity table, and no record in Outbox table.
        
        Goal: This function checks if updating a centre activity with no actual changes does NOT create an outbox event.
        """
        # Create centre activity
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
            created_by_id="test-user-1"
        )
        centre_activity = create_centre_activity(
            db=integration_db,
            centre_activity_data=centre_activity_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Centre Activity ID: {centre_activity.id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(centre_activity.id)
        ).delete()
        integration_db.commit()
        
        # "Update" with same values (no actual changes)
        update_data = CentreActivityUpdate(
            id=centre_activity.id,
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
            is_deleted=False,
            modified_by_id="test-user-1",
            modified_date=datetime.now()
        )
        update_centre_activity(
            db=integration_db,
            centre_activity_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: No-change update processed")
        
        # No new CENTRE_ACTIVITY_UPDATED event should be created
        updated_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "CENTRE_ACTIVITY_UPDATED",
            OutboxEvent.aggregate_id == str(centre_activity.id)
        ).first()
        
        assert updated_event is None
        print(f"DONE: Verified no UPDATE event created")

class TestCentreActivityDeleteOutbox:    
    def test_delete_centre_activity_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing centre activity
        WHEN: delete_centre_activity is called
        THEN: OutboxEvent records deletion atomically
        
        Goal: This function checks if soft-deleting a centre activity creates an outbox event with the deletion info.
        """
        # Create centre activity
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
            created_by_id="test-user-1"
        )
        centre_activity = create_centre_activity(
            db=integration_db,
            centre_activity_data=centre_activity_data,
            current_user_info=mock_user
        )
        original_id = centre_activity.id
        
        print(f"\nDONE: Created Centre Activity ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Delete centre activity
        deleted_centre_activity = delete_centre_activity(
            db=integration_db,
            centre_activity_id=original_id,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Centre Activity ID: {original_id}")
        
        # Assertions: Centre Activity soft-deleted
        assert deleted_centre_activity.is_deleted == True
        refreshed = get_centre_activity_by_id(
            db=integration_db,
            centre_activity_id=original_id,
            include_deleted=True
        )
        assert refreshed.is_deleted == True
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "CENTRE_ACTIVITY_DELETED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.centre_activity.deleted.{original_id}"
        
        print(f"DONE: Created DELETE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload
        payload = outbox_event.get_payload()
        assert payload["deleted_by"] == "test-user-1"
        assert "centre_activity_data" in payload

class TestOutboxTransactionAtomicity:
    """Test that centre activity and outbox events are created atomically"""
    
    def test_centre_activity_and_outbox_created_together_or_not_at_all(self, integration_db, mock_user):
        """
        GIVEN: Create operation succeeds
        WHEN: Transaction is committed
        THEN: Both centre activity and outbox event exist
        
        Goal: This function checks if the creation of centre activity and outbox event are atomic - both created or neither.
        """
        initial_centre_activity_count = integration_db.query(CentreActivity).count()
        initial_outbox_count = integration_db.query(OutboxEvent).count()
        
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
            created_by_id="test-user-1"
        )
        
        centre_activity = create_centre_activity(
            db=integration_db,
            centre_activity_data=centre_activity_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Centre Activity ID: {centre_activity.id}")
        
        final_centre_activity_count = integration_db.query(CentreActivity).count()
        final_outbox_count = integration_db.query(OutboxEvent).count()
        
        # Both should be created together
        assert final_centre_activity_count == initial_centre_activity_count + 1
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Centre Activity count: {initial_centre_activity_count} → {final_centre_activity_count}")
        print(f"DONE: Outbox count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify they reference the same aggregate
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(centre_activity.id)
        ).first()
        assert outbox is not None
        
        print(f"DONE: Verified atomic creation")

    def test_centre_activity_update_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing centre activity that will be updated
        WHEN: Update operation succeeds
        THEN: Centre Activity modification and outbox event creation occur atomically
        
        Goal: This function checks if updating a centre activity creates an outbox event with the same data.
        """
        # Create initial centre activity
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
            created_by_id="test-user-1"
        )
        centre_activity = create_centre_activity(
            db=integration_db,
            centre_activity_data=centre_activity_data,
            current_user_info=mock_user
        )
        original_id = centre_activity.id
        original_modified_date = centre_activity.modified_date
        
        print(f"\nDONE: Created Centre Activity ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "CENTRE_ACTIVITY_UPDATED"
        ).count()
        
        # Update centre activity
        update_data = CentreActivityUpdate(
            id=original_id,
            activity_id=1,
            is_compulsory=False,
            is_fixed=True,
            is_group=True,  # Changed
            start_date=date.today(),
            end_date=date(2999, 12, 31),
            min_duration=60,
            max_duration=60,
            min_people_req=3,  # Changed
            fixed_time_slots="10:00-11:00",  # Changed
            is_deleted=False,
            modified_by_id="test-user-1",
            modified_date=datetime.now()
        )
        updated_centre_activity = update_centre_activity(
            db=integration_db,
            centre_activity_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Centre Activity ID: {original_id}")
        
        # Verify centre activity was actually modified in the database
        refreshed_centre_activity = get_centre_activity_by_id(
            db=integration_db,
            centre_activity_id=original_id,
            include_deleted=False
        )
        assert refreshed_centre_activity.is_group == True
        assert refreshed_centre_activity.min_people_req == 3
        assert refreshed_centre_activity.fixed_time_slots == "10:00-11:00"
        assert refreshed_centre_activity.modified_date > original_modified_date
        assert refreshed_centre_activity.modified_by_id == "test-user-1"
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "CENTRE_ACTIVITY_UPDATED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Centre Activity modified and Outbox UPDATED count: {initial_outbox_count} -> {final_outbox_count}")
        
        # Verify the outbox event references the updated centre activity
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "CENTRE_ACTIVITY_UPDATED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.centre_activity.updated.{original_id}"
        
        # Verify payload reflects the actual changes
        payload = outbox.get_payload()
        assert "changes" in payload
        assert "is_group" in payload["changes"]
        assert payload["changes"]["is_group"]["old"] == False
        assert payload["changes"]["is_group"]["new"] == True
        
        print(f"DONE: Verified atomic update - centre activity modified and outbox event created together")

    def test_centre_activity_delete_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing centre activity that will be deleted
        WHEN: Delete operation succeeds
        THEN: Centre Activity soft-deletion and outbox event creation occur atomically
        
        Goal: This function checks if soft-deleting a centre activity creates an outbox event with the same deletion info.
        """
        # Create initial centre activity
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
            created_by_id="test-user-1"
        )
        centre_activity = create_centre_activity(
            db=integration_db,
            centre_activity_data=centre_activity_data,
            current_user_info=mock_user
        )
        original_id = centre_activity.id
        original_modified_date = centre_activity.modified_date
        
        print(f"\nDONE: Created Centre Activity ID: {original_id}")
        
        # Verify centre activity is not deleted initially
        assert centre_activity.is_deleted == False
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "CENTRE_ACTIVITY_DELETED"
        ).count()
        
        # Delete centre activity (soft delete)
        deleted_centre_activity = delete_centre_activity(
            db=integration_db,
            centre_activity_id=original_id,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Centre Activity ID: {original_id}")
        
        # Verify centre activity was soft-deleted in the database
        refreshed_centre_activity = get_centre_activity_by_id(
            db=integration_db,
            centre_activity_id=original_id,
            include_deleted=True
        )
        assert refreshed_centre_activity is not None
        assert refreshed_centre_activity.is_deleted == True
        assert refreshed_centre_activity.modified_date > original_modified_date
        assert refreshed_centre_activity.modified_by_id == "test-user-1"
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "CENTRE_ACTIVITY_DELETED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Centre Activity soft-deleted and Outbox DELETED count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify the outbox event references the deleted centre activity
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "CENTRE_ACTIVITY_DELETED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.centre_activity.deleted.{original_id}"
        
        # Verify payload contains deletion information
        payload = outbox.get_payload()
        assert payload["centre_activity_id"] == original_id
        assert payload["deleted_by"] == "test-user-1"
        assert "centre_activity_data" in payload
        
        print(f"DONE: Verified atomic deletion - centre activity soft-deleted and outbox event created together")
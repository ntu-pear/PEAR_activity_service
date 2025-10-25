"""
Integration tests for Activity Service (Publisher) Outbox Pattern
Tests the flow: Activity CRUD -> OUTBOX_EVENTS table creation

Run Pytest with command: 
1. Run everything: pytest tests/integration/test_activity_outbox_integration.py -v -s
2. Run specific test class: pytest tests/integration/test_activity_outbox_integration.py::TestActivityCreateOutbox -v -s
3. Run specific test function: pytest tests/integration/test_activity_outbox_integration.py::TestActivityCreateOutbox::test_create_activity_creates_outbox_event -v -s

"""

import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.crud.activity_crud import (
    create_activity,
    delete_activity_by_id,
    get_activity_by_id,
    update_activity_by_id,
)
from app.database import SessionLocal
from app.models.activity_model import Activity
from app.models.outbox_model import OutboxEvent
from app.schemas.activity_schema import ActivityCreate, ActivityUpdate


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

class TestActivityCreateOutbox:    
    def test_create_activity_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: Activity data
        WHEN: create_activity is called
        THEN: Activity and OutboxEvent are created atomically
        
        Goal: Check if the creation of activity also creates an outbox event. This function checks if the created records are the same
        
        """
        activity_data = ActivityCreate(
            title="Testing Activity",
            description="Test Description"
        )
        
        # Create activity
        activity = create_activity(
            db=integration_db,
            activity_in=activity_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity ID: {activity.id}")
        print(f"  Title: {activity.title}")
        print(f"  Created By: {activity.created_by_id}")
        
        # Assertions: Activity created
        assert activity.id is not None
        assert activity.title == "Testing Activity"
        assert activity.created_by_id == "test-user-1"
        assert activity.is_deleted == False
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(activity.id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.event_type == "ACTIVITY_CREATED"
        assert outbox_event.aggregate_id == str(activity.id)
        assert outbox_event.routing_key == f"activity.created.{activity.id}"
        
        print(f"DONE: Created Outbox Event ID: {outbox_event.id}")
        print(f"  Event Type: {outbox_event.event_type}")
        print(f"  Correlation ID: {outbox_event.correlation_id}")
        
        # Verify payload structure
        payload = outbox_event.get_payload()
        assert payload["event_type"] == "ACTIVITY_CREATED"
        assert payload["activity_id"] == activity.id
        assert payload["created_by"] == "test-user-1"
        assert "correlation_id" in payload
        assert "timestamp" in payload
    
    def test_duplicate_activity_fails_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing activity with title "Duplicate"
        WHEN: create_activity is called with same title
        THEN: HTTPException raised and no additional outbox event created
        
        Goal: This function checks if the creation of duplicate activity is rejected properly and no outbox event is created.
        """
        activity_data = ActivityCreate(
            title="Duplicate Title Test",
            description="Desc"
        )
        
        # Create first activity
        activity1 = create_activity(
            db=integration_db,
            activity_in=activity_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created first activity ID: {activity1.id}")
        
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_CREATED"
        ).count()
        
        # Attempt to create duplicate
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            create_activity(
                db=integration_db,
                activity_in=activity_data,
                current_user_info=mock_user
            )
        
        assert exc_info.value.status_code == 400
        
        print(f"DONE: Duplicate creation properly rejected")
        
        # Verify no additional outbox events created
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_CREATED"
        ).count()
        assert final_outbox_count == initial_outbox_count

class TestActivityUpdateOutbox:    
    def test_update_activity_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing activity
        WHEN: update_activity_by_id is called with changes
        THEN: OutboxEvent records changes atomically
        
        Goal: This function checks if updating an activity creates an outbox event with the changes.
        """
        # Create initial activity
        activity_data = ActivityCreate(
            title="Original Title",
            description="Original Desc"
        )
        activity = create_activity(
            db=integration_db,
            activity_in=activity_data,
            current_user_info=mock_user
        )
        original_id = activity.id
        
        print(f"\nDONE: Created Activity ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Update activity - include is_deleted as it's required in schema
        update_data = ActivityUpdate(
            id=original_id,
            title="Updated Title",
            description="Updated Desc",
            is_deleted=False
        )
        updated_activity = update_activity_by_id(
            db=integration_db,
            activity_id=original_id,
            activity_in=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Activity ID: {original_id}")
        
        # Assertions: Activity updated
        assert updated_activity.title == "Updated Title"
        assert updated_activity.description == "Updated Desc"
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_UPDATED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.updated.{original_id}"
        
        print(f"DONE: Created UPDATE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload contains changes
        payload = outbox_event.get_payload()
        assert "changes" in payload
        assert "title" in payload["changes"]
        assert payload["changes"]["title"]["old"] == "Original Title"
        assert payload["changes"]["title"]["new"] == "Updated Title"
    
    def test_update_with_no_changes_does_not_create_outbox(self, integration_db, mock_user):
        """
        GIVEN: An existing activity
        WHEN: update_activity_by_id is called with no actual changes
        THEN: No new OutboxEvent is created for ACTIVITY_UPDATED
        NOTE: This function will create one extra record in the Activity table, and no record in Outbox table.
        
        Goal: This function checks if updating an activity with no actual changes does NOT create an outbox event.
        """
        # Create activity
        activity_data = ActivityCreate(
            title="Test No Changes",
            description="Desc"
        )
        activity = create_activity(
            db=integration_db,
            activity_in=activity_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity ID: {activity.id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(activity.id)
        ).delete()
        integration_db.commit()
        
        # "Update" with same values (no actual changes)
        update_data = ActivityUpdate(
            id=activity.id,
            title="Test No Changes",
            description="Desc",
            is_deleted=False
        )
        update_activity_by_id(
            db=integration_db,
            activity_id=activity.id,
            activity_in=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: No-change update processed")
        
        # No new ACTIVITY_UPDATED event should be created
        updated_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_UPDATED",
            OutboxEvent.aggregate_id == str(activity.id)
        ).first()
        
        assert updated_event is None
        print(f"DONE: Verified no UPDATE event created")
    
    def test_update_nonexistent_activity_fails(self, integration_db, mock_user):
        """
        GIVEN: Non-existent activity ID
        WHEN: update_activity_by_id is called
        THEN: HTTPException raised and no outbox event created
        
        Goal: This function checks if updating a non-existent activity is rejected properly and no outbox event is created.
        """
        initial_outbox_count = integration_db.query(OutboxEvent).count()
        
        update_data = ActivityUpdate(
            id=99999,
            title="Updated",
            description="Updated Desc",
            is_deleted=False
        )
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            update_activity_by_id(
                db=integration_db,
                activity_id=99999,
                activity_in=update_data,
                current_user_info=mock_user
            )
        
        assert exc_info.value.status_code == 404
        
        print(f"\nDONE: Update of non-existent activity properly rejected")
        
        # No outbox event created
        final_outbox_count = integration_db.query(OutboxEvent).count()
        assert final_outbox_count == initial_outbox_count

class TestActivityDeleteOutbox:    
    def test_delete_activity_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing activity
        WHEN: delete_activity_by_id is called
        THEN: OutboxEvent records deletion atomically
        
        Goal: This function checks if soft-deleting an activity creates an outbox event with the deletion info.
        """
        # Create activity
        activity_data = ActivityCreate(
            title="To Delete",
            description="Desc"
        )
        activity = create_activity(
            db=integration_db,
            activity_in=activity_data,
            current_user_info=mock_user
        )
        original_id = activity.id
        
        print(f"\nDONE: Created Activity ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Delete activity
        deleted_activity = delete_activity_by_id(
            db=integration_db,
            activity_id=original_id,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Activity ID: {original_id}")
        
        # Assertions: Activity soft-deleted
        assert deleted_activity.is_deleted == True
        refreshed = get_activity_by_id(
            db=integration_db,
            activity_id=original_id,
            include_deleted=True
        )
        assert refreshed.is_deleted == True
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_DELETED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.deleted.{original_id}"
        
        print(f"DONE: Created DELETE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload
        payload = outbox_event.get_payload()
        assert payload["deleted_by"] == "test-user-1"
        assert "activity_data" in payload
    
    def test_delete_nonexistent_activity_fails(self, integration_db, mock_user):
        """
        GIVEN: Non-existent activity ID
        WHEN: delete_activity_by_id is called
        THEN: HTTPException raised and no outbox event created
        
        Goal: This function checks if deleting a non-existent activity is rejected properly and no outbox event is created.
        """
        initial_outbox_count = integration_db.query(OutboxEvent).count()
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            delete_activity_by_id(
                db=integration_db,
                activity_id=99999,
                current_user_info=mock_user
            )
        
        assert exc_info.value.status_code == 404
        
        print(f"\nDONE: Delete of non-existent activity properly rejected")
        
        # No outbox event created
        final_outbox_count = integration_db.query(OutboxEvent).count()
        assert final_outbox_count == initial_outbox_count

class TestOutboxTransactionAtomicity:
    """Test that activity and outbox events are created atomically"""
    
    def test_activity_and_outbox_created_together_or_not_at_all(self, integration_db, mock_user):
        """
        GIVEN: Create operation succeeds
        WHEN: Transaction is committed
        THEN: Both activity and outbox event exist
        
        Goal: This function checks if the creation of activity and outbox event are atomic - both created or neither.
        """
        initial_activity_count = integration_db.query(Activity).count()
        initial_outbox_count = integration_db.query(OutboxEvent).count()
        
        activity_data = ActivityCreate(
            title="Atomic Test",
            description="Desc"
        )
        
        activity = create_activity(
            db=integration_db,
            activity_in=activity_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity ID: {activity.id}")
        
        final_activity_count = integration_db.query(Activity).count()
        final_outbox_count = integration_db.query(OutboxEvent).count()
        
        # Both should be created together
        assert final_activity_count == initial_activity_count + 1
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Activity count: {initial_activity_count} → {final_activity_count}")
        print(f"DONE: Outbox count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify they reference the same aggregate
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(activity.id)
        ).first()
        assert outbox is not None
        
        print(f"DONE: Verified atomic creation")

    def test_activity_update_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing activity that will be updated
        WHEN: Update operation succeeds
        THEN: Activity modification and outbox event creation occur atomically
        
        Goal: This function checks if updating an activity creates an outbox event with the same data.
        """
        # Create initial activity
        activity_data = ActivityCreate(
            title="Atomic Update Test",
            description="Original Description"
        )
        activity = create_activity(
            db=integration_db,
            activity_in=activity_data,
            current_user_info=mock_user
        )
        original_id = activity.id
        original_modified_date = activity.modified_date
        
        print(f"\nDONE: Created Activity ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_UPDATED"
        ).count()
        
        # Update activity
        update_data = ActivityUpdate(
            id=original_id,
            title="Atomically Updated Title",
            description="Atomically Updated Description",
            is_deleted=False
        )
        updated_activity = update_activity_by_id(
            db=integration_db,
            activity_id=original_id,
            activity_in=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Activity ID: {original_id}")
        
        # Verify activity was actually modified in the database
        refreshed_activity = get_activity_by_id(
            db=integration_db,
            activity_id=original_id,
            include_deleted=False
        )
        assert refreshed_activity.title == "Atomically Updated Title"
        assert refreshed_activity.description == "Atomically Updated Description"
        assert refreshed_activity.modified_date > original_modified_date  # Timestamp changed
        assert refreshed_activity.modified_by_id == "test-user-1"
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_UPDATED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Activity modified and Outbox UPDATED count: {initial_outbox_count} -> {final_outbox_count}")
        
        # Verify the outbox event references the updated activity
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "ACTIVITY_UPDATED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.updated.{original_id}"
        assert outbox.created_by == "test-user-1"
        
        # Verify payload reflects the actual changes
        payload = outbox.get_payload()
        assert payload["activity_id"] == original_id
        assert "changes" in payload
        assert "title" in payload["changes"]
        assert payload["changes"]["title"]["old"] == "Atomic Update Test"
        assert payload["changes"]["title"]["new"] == "Atomically Updated Title"
        
        print(f"DONE: Verified atomic update - activity modified and outbox event created together")


    def test_activity_delete_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing activity that will be deleted
        WHEN: Delete operation succeeds
        THEN: Activity soft-deletion and outbox event creation occur atomically
        
        Goal: This function checks if soft-deleting an activity creates an outbox event with the same deletion info.
        """
        # Create initial activity
        activity_data = ActivityCreate(
            title="Atomic Delete Test",
            description="To be deleted atomically"
        )
        activity = create_activity(
            db=integration_db,
            activity_in=activity_data,
            current_user_info=mock_user
        )
        original_id = activity.id
        original_modified_date = activity.modified_date
        
        print(f"\nDONE: Created Activity ID: {original_id}")
        
        # Verify activity is not deleted initially
        assert activity.is_deleted == False
        
        # Clear outbox from creation - since we only want to look at the deletion event
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_DELETED"
        ).count()
        
        # Delete activity (soft delete)
        deleted_activity = delete_activity_by_id(
            db=integration_db,
            activity_id=original_id,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Activity ID: {original_id}")
        
        # Verify activity was soft-deleted in the database
        refreshed_activity = get_activity_by_id(
            db=integration_db,
            activity_id=original_id,
            include_deleted=True  # Must include deleted to retrieve it
        )
        assert refreshed_activity is not None
        assert refreshed_activity.is_deleted == True
        assert refreshed_activity.modified_date > original_modified_date  # Timestamp changed
        assert refreshed_activity.modified_by_id == "test-user-1"
        
        # Verify the activity is NOT retrievable without include_deleted
        non_deleted_activity = get_activity_by_id(
            db=integration_db,
            activity_id=original_id,
            include_deleted=False
        )
        assert non_deleted_activity is None  # Should not be found
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_DELETED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Activity soft-deleted and Outbox DELETED count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify the outbox event references the deleted activity
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "ACTIVITY_DELETED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.deleted.{original_id}"
        assert outbox.created_by == "test-user-1"
        
        # Verify payload contains deletion information
        payload = outbox.get_payload()
        assert payload["activity_id"] == original_id
        assert payload["deleted_by"] == "test-user-1"
        assert "activity_data" in payload
        assert payload["activity_data"]["title"] == "Atomic Delete Test"
        
        # This verifies the actual activity in DB has is_deleted=True - confirms the soft-delete actually happened
        final_activity_state = get_activity_by_id(
            db=integration_db,
            activity_id=original_id,
            include_deleted=True
        )
        assert final_activity_state.is_deleted == True  # The actual deletion happened
        
        print(f"DONE: Verified atomic deletion - activity soft-deleted and outbox event created together")
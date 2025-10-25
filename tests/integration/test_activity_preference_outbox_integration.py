"""
Integration tests for Activity Preference Service (Publisher) Outbox Pattern
Tests the flow: Activity Preference CRUD -> OUTBOX_EVENTS table creation

Run Pytest with command: 
1. Run everything: pytest tests/integration/test_activity_preference_outbox_integration.py -v -s
2. Run specific test class: pytest tests/integration/test_activity_preference_outbox_integration.py::TestActivityPreferenceCreateOutbox -v -s
3. Run specific test function: pytest tests/integration/test_activity_preference_outbox_integration.py::TestActivityPreferenceCreateOutbox::test_create_preference_creates_outbox_event -v -s

"""

import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.crud.centre_activity_preference_crud import (
    create_centre_activity_preference,
    delete_centre_activity_preference_by_id,
    get_centre_activity_preference_by_id,
    update_centre_activity_preference_by_id,
)
from app.database import SessionLocal
from app.models.centre_activity_preference_model import CentreActivityPreference
from app.models.outbox_model import OutboxEvent
from app.schemas.centre_activity_preference_schema import (
    CentreActivityPreferenceCreate,
    CentreActivityPreferenceUpdate,
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
        "fullname": "Integration Test User",
        "bearer_token": "test-token-123"
    }

class TestActivityPreferenceCreateOutbox:    
    def test_create_preference_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: Activity Preference data
        WHEN: create_centre_activity_preference is called
        THEN: CentreActivityPreference and OutboxEvent are created atomically
        
        Goal: Check if the creation of activity preference also creates an outbox event. This function checks if the created records are the same
        
        """
        preference_data = CentreActivityPreferenceCreate(
            centre_activity_id=1,
            patient_id=1,
            is_like=1,
            created_by_id="test-user-1"
        )
        
        # Create activity preference
        preference = create_centre_activity_preference(
            db=integration_db,
            centre_activity_preference_data=preference_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity Preference ID: {preference.id}")
        print(f"  Centre Activity ID: {preference.centre_activity_id}")
        print(f"  Patient ID: {preference.patient_id}")
        print(f"  Is Like: {preference.is_like}")
        print(f"  Created By: {preference.created_by_id}")
        
        # Assertions: Preference created
        assert preference.id is not None
        assert preference.centre_activity_id == 1
        assert preference.patient_id == 1
        assert preference.is_like == 1
        assert preference.created_by_id == "test-user-1"
        assert preference.is_deleted == False
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(preference.id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.event_type == "ACTIVITY_PREFERENCE_CREATED"
        assert outbox_event.aggregate_id == str(preference.id)
        assert outbox_event.routing_key == f"activity.preference.created.{preference.id}"
        
        print(f"DONE: Created Outbox Event ID: {outbox_event.id}")
        print(f"  Event Type: {outbox_event.event_type}")
        print(f"  Correlation ID: {outbox_event.correlation_id}")
        
        # Verify payload structure
        payload = outbox_event.get_payload()
        assert payload["event_type"] == "ACTIVITY_PREFERENCE_CREATED"
        assert payload["preference_id"] == preference.id
        assert payload["created_by"] == "test-user-1"
        assert "correlation_id" in payload
        assert "timestamp" in payload

class TestActivityPreferenceUpdateOutbox:    
    def test_update_preference_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing activity preference
        WHEN: update_centre_activity_preference_by_id is called with changes
        THEN: OutboxEvent records changes atomically
        
        Goal: This function checks if updating an activity preference creates an outbox event with the changes.
        """
        # Create initial preference
        preference_data = CentreActivityPreferenceCreate(
            centre_activity_id=1,
            patient_id=1,
            is_like=1,
            created_by_id="test-user-1"
        )
        preference = create_centre_activity_preference(
            db=integration_db,
            centre_activity_preference_data=preference_data,
            current_user_info=mock_user
        )
        original_id = preference.id
        
        print(f"\nDONE: Created Activity Preference ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Update preference
        update_data = CentreActivityPreferenceUpdate(
            id=original_id,
            centre_activity_id=1,
            patient_id=1,
            is_like=-1,  # Changed from 1 to -1
            is_deleted=False,
            modified_by_id="test-user-1",
            modified_date=datetime.now()
        )
        updated_preference = update_centre_activity_preference_by_id(
            db=integration_db,
            centre_activity_preference_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Activity Preference ID: {original_id}")
        
        # Assertions: Preference updated
        assert updated_preference.is_like == -1
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_PREFERENCE_UPDATED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.preference.updated.{original_id}"
        
        print(f"DONE: Created UPDATE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload contains changes
        payload = outbox_event.get_payload()
        assert "changes" in payload
        assert "is_like" in payload["changes"]
        assert payload["changes"]["is_like"]["old"] == 1
        assert payload["changes"]["is_like"]["new"] == -1
    
    def test_update_with_no_changes_does_not_create_outbox(self, integration_db, mock_user):
        """
        GIVEN: An existing activity preference
        WHEN: update_centre_activity_preference_by_id is called with no actual changes
        THEN: No new OutboxEvent is created for ACTIVITY_PREFERENCE_UPDATED
        NOTE: This function will create one extra record in the CentreActivityPreference table, and no record in Outbox table.
        
        Goal: This function checks if updating an activity preference with no actual changes does NOT create an outbox event.
        """
        # Create preference
        preference_data = CentreActivityPreferenceCreate(
            centre_activity_id=1,
            patient_id=1,
            is_like=0,
            created_by_id="test-user-1"
        )
        preference = create_centre_activity_preference(
            db=integration_db,
            centre_activity_preference_data=preference_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity Preference ID: {preference.id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(preference.id)
        ).delete()
        integration_db.commit()
        
        # "Update" with same values (no actual changes)
        update_data = CentreActivityPreferenceUpdate(
            id=preference.id,
            centre_activity_id=1,
            patient_id=1,
            is_like=0,
            is_deleted=False,
            modified_by_id="test-user-1",
            modified_date=datetime.now()
        )
        update_centre_activity_preference_by_id(
            db=integration_db,
            centre_activity_preference_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: No-change update processed")
        
        # No new ACTIVITY_PREFERENCE_UPDATED event should be created
        updated_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_PREFERENCE_UPDATED",
            OutboxEvent.aggregate_id == str(preference.id)
        ).first()
        
        assert updated_event is None
        print(f"DONE: Verified no UPDATE event created")

class TestActivityPreferenceDeleteOutbox:    
    def test_delete_preference_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing activity preference
        WHEN: delete_centre_activity_preference_by_id is called
        THEN: OutboxEvent records deletion atomically
        
        Goal: This function checks if soft-deleting an activity preference creates an outbox event with the deletion info.
        """
        # Create preference
        preference_data = CentreActivityPreferenceCreate(
            centre_activity_id=1,
            patient_id=1,
            is_like=1,
            created_by_id="test-user-1"
        )
        preference = create_centre_activity_preference(
            db=integration_db,
            centre_activity_preference_data=preference_data,
            current_user_info=mock_user
        )
        original_id = preference.id
        
        print(f"\nDONE: Created Activity Preference ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Delete preference
        deleted_preference = delete_centre_activity_preference_by_id(
            centre_activity_preference_id=original_id,
            db=integration_db,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Activity Preference ID: {original_id}")
        
        # Assertions: Preference soft-deleted
        assert deleted_preference.is_deleted == True
        refreshed = get_centre_activity_preference_by_id(
            db=integration_db,
            centre_activity_preference_id=original_id,
            include_deleted=True
        )
        assert refreshed.is_deleted == True
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_PREFERENCE_DELETED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.preference.deleted.{original_id}"
        
        print(f"DONE: Created DELETE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload
        payload = outbox_event.get_payload()
        assert payload["deleted_by"] == "test-user-1"
        assert "preference_data" in payload

class TestOutboxTransactionAtomicity:
    """Test that activity preference and outbox events are created atomically"""
    
    def test_preference_and_outbox_created_together_or_not_at_all(self, integration_db, mock_user):
        """
        GIVEN: Create operation succeeds
        WHEN: Transaction is committed
        THEN: Both preference and outbox event exist
        
        Goal: This function checks if the creation of activity preference and outbox event are atomic - both created or neither.
        """
        initial_preference_count = integration_db.query(CentreActivityPreference).count()
        initial_outbox_count = integration_db.query(OutboxEvent).count()
        
        preference_data = CentreActivityPreferenceCreate(
            centre_activity_id=1,
            patient_id=1,
            is_like=1,
            created_by_id="test-user-1"
        )
        
        preference = create_centre_activity_preference(
            db=integration_db,
            centre_activity_preference_data=preference_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity Preference ID: {preference.id}")
        
        final_preference_count = integration_db.query(CentreActivityPreference).count()
        final_outbox_count = integration_db.query(OutboxEvent).count()
        
        # Both should be created together
        assert final_preference_count == initial_preference_count + 1
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Preference count: {initial_preference_count} → {final_preference_count}")
        print(f"DONE: Outbox count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify they reference the same aggregate
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(preference.id)
        ).first()
        assert outbox is not None
        
        print(f"DONE: Verified atomic creation")

    def test_preference_update_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing activity preference that will be updated
        WHEN: Update operation succeeds
        THEN: Preference modification and outbox event creation occur atomically
        
        Goal: This function checks if updating an activity preference creates an outbox event with the same data.
        """
        # Create initial preference
        preference_data = CentreActivityPreferenceCreate(
            centre_activity_id=1,
            patient_id=1,
            is_like=0,
            created_by_id="test-user-1"
        )
        preference = create_centre_activity_preference(
            db=integration_db,
            centre_activity_preference_data=preference_data,
            current_user_info=mock_user
        )
        original_id = preference.id
        original_modified_date = preference.modified_date
        
        print(f"\nDONE: Created Activity Preference ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_PREFERENCE_UPDATED"
        ).count()
        
        # Update preference
        update_data = CentreActivityPreferenceUpdate(
            id=original_id,
            centre_activity_id=1,
            patient_id=1,
            is_like=1,  # Changed from 0 to 1
            is_deleted=False,
            modified_by_id="test-user-1",
            modified_date=datetime.now()
        )
        updated_preference = update_centre_activity_preference_by_id(
            db=integration_db,
            centre_activity_preference_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Activity Preference ID: {original_id}")
        
        # Verify preference was actually modified in the database
        refreshed_preference = get_centre_activity_preference_by_id(
            db=integration_db,
            centre_activity_preference_id=original_id,
            include_deleted=False
        )
        assert refreshed_preference.is_like == 1
        assert refreshed_preference.modified_date > original_modified_date
        assert refreshed_preference.modified_by_id == "test-user-1"
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_PREFERENCE_UPDATED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Preference modified and Outbox UPDATED count: {initial_outbox_count} -> {final_outbox_count}")
        
        # Verify the outbox event references the updated preference
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "ACTIVITY_PREFERENCE_UPDATED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.preference.updated.{original_id}"
        
        print(f"DONE: Verified atomic update - preference modified and outbox event created together")

    def test_preference_delete_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing activity preference that will be deleted
        WHEN: Delete operation succeeds
        THEN: Preference soft-deletion and outbox event creation occur atomically
        
        Goal: This function checks if soft-deleting an activity preference creates an outbox event with the same deletion info.
        """
        # Create initial preference
        preference_data = CentreActivityPreferenceCreate(
            centre_activity_id=1,
            patient_id=1,
            is_like=1,
            created_by_id="test-user-1"
        )
        preference = create_centre_activity_preference(
            db=integration_db,
            centre_activity_preference_data=preference_data,
            current_user_info=mock_user
        )
        original_id = preference.id
        original_modified_date = preference.modified_date
        
        print(f"\nDONE: Created Activity Preference ID: {original_id}")
        
        # Verify preference is not deleted initially
        assert preference.is_deleted == False
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_PREFERENCE_DELETED"
        ).count()
        
        # Delete preference (soft delete)
        deleted_preference = delete_centre_activity_preference_by_id(
            centre_activity_preference_id=original_id,
            db=integration_db,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Activity Preference ID: {original_id}")
        
        # Verify preference was soft-deleted in the database
        refreshed_preference = get_centre_activity_preference_by_id(
            db=integration_db,
            centre_activity_preference_id=original_id,
            include_deleted=True
        )
        assert refreshed_preference is not None
        assert refreshed_preference.is_deleted == True
        assert refreshed_preference.modified_date > original_modified_date
        assert refreshed_preference.modified_by_id == "test-user-1"
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_PREFERENCE_DELETED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Preference soft-deleted and Outbox DELETED count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify the outbox event references the deleted preference
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "ACTIVITY_PREFERENCE_DELETED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.preference.deleted.{original_id}"
        
        # Verify payload contains deletion information
        payload = outbox.get_payload()
        assert payload["preference_id"] == original_id
        assert payload["deleted_by"] == "test-user-1"
        assert "preference_data" in payload
        
        print(f"DONE: Verified atomic deletion - preference soft-deleted and outbox event created together")
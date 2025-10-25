"""
Integration tests for Activity Exclusion Service (Publisher) Outbox Pattern
Tests the flow: Activity Exclusion CRUD -> OUTBOX_EVENTS table creation

Run Pytest with command: 
1. Run everything: pytest tests/integration/test_activity_exclusion_outbox_integration.py -v -s
2. Run specific test class: pytest tests/integration/test_activity_exclusion_outbox_integration.py::TestActivityExclusionCreateOutbox -v -s
3. Run specific test function: pytest tests/integration/test_activity_exclusion_outbox_integration.py::TestActivityExclusionCreateOutbox::test_create_exclusion_creates_outbox_event -v -s

** If there are any errors when running any of the integration tests, ensure that the ACTIVITY(id=1) and CENTRE_ACTIVITY(id=1, and links to Activity_id=1 via FK) exists. You can insert them manually into the testing DB if needed.
*** Use the Helper Functions in conftest.py (in the integration file) to create the base ACTIVITY and CENTRE_ACTIVITY records if needed.
"""

import json
from datetime import date, datetime

import pytest
from sqlalchemy.orm import Session

from app.crud.centre_activity_exclusion_crud import (
    create_centre_activity_exclusion,
    delete_centre_activity_exclusion,
    get_centre_activity_exclusion_by_id,
    update_centre_activity_exclusion,
)
from app.database import SessionLocal
from app.models.centre_activity_exclusion_model import CentreActivityExclusion
from app.models.outbox_model import OutboxEvent
from app.schemas.centre_activity_exclusion_schema import (
    CentreActivityExclusionCreate,
    CentreActivityExclusionUpdate,
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

class TestActivityExclusionCreateOutbox:    
    def test_create_exclusion_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: Activity Exclusion data
        WHEN: create_centre_activity_exclusion is called
        THEN: CentreActivityExclusion and OutboxEvent are created atomically
        
        Goal: Check if the creation of activity exclusion also creates an outbox event. This function checks if the created records are the same
        
        """
        exclusion_data = CentreActivityExclusionCreate(
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="Test Exclusion",
            start_date=date.today(),
            end_date=None
        )
        
        # Create activity exclusion
        exclusion = create_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=exclusion_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity Exclusion ID: {exclusion.id}")
        print(f"  Centre Activity ID: {exclusion.centre_activity_id}")
        print(f"  Patient ID: {exclusion.patient_id}")
        print(f"  Created By: {exclusion.created_by_id}")
        
        # Assertions: Exclusion created
        assert exclusion.id is not None
        assert exclusion.centre_activity_id == 1
        assert exclusion.patient_id == 1
        assert exclusion.created_by_id == "test-user-1"
        assert exclusion.is_deleted == False
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(exclusion.id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.event_type == "ACTIVITY_EXCLUSION_CREATED"
        assert outbox_event.aggregate_id == str(exclusion.id)
        assert outbox_event.routing_key == f"activity.centre_activity_exclusion.created.{exclusion.id}"
        
        print(f"DONE: Created Outbox Event ID: {outbox_event.id}")
        print(f"  Event Type: {outbox_event.event_type}")
        print(f"  Correlation ID: {outbox_event.correlation_id}")
        
        # Verify payload structure
        payload = outbox_event.get_payload()
        assert payload["event_type"] == "ACTIVITY_EXCLUSION_CREATED"
        assert payload["exclusion_id"] == exclusion.id
        assert payload["created_by"] == "test-user-1"
        assert "correlation_id" in payload
        assert "timestamp" in payload

class TestActivityExclusionUpdateOutbox:    
    def test_update_exclusion_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing activity exclusion
        WHEN: update_centre_activity_exclusion is called with changes
        THEN: OutboxEvent records changes atomically
        
        Goal: This function checks if updating an activity exclusion creates an outbox event with the changes.
        """
        # Create initial exclusion
        exclusion_data = CentreActivityExclusionCreate(
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="Original Remarks",
            start_date=date.today(),
            end_date=None
        )
        exclusion = create_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=exclusion_data,
            current_user_info=mock_user
        )
        original_id = exclusion.id
        
        print(f"\nDONE: Created Activity Exclusion ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Update exclusion
        update_data = CentreActivityExclusionUpdate(
            id=original_id,
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="Updated Remarks",
            start_date=date.today(),
            end_date=None,
            is_deleted=False,
            modified_by_id="test-user-1"
        )
        updated_exclusion = update_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Activity Exclusion ID: {original_id}")
        
        # Assertions: Exclusion updated
        assert updated_exclusion.exclusion_remarks == "Updated Remarks"
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_EXCLUSION_UPDATED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.centre_activity_exclusion.updated.{original_id}"
        
        print(f"DONE: Created UPDATE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload contains changes
        payload = outbox_event.get_payload()
        assert "changes" in payload
        assert "exclusion_remarks" in payload["changes"]
        assert payload["changes"]["exclusion_remarks"]["old"] == "Original Remarks"
        assert payload["changes"]["exclusion_remarks"]["new"] == "Updated Remarks"
    
    def test_update_with_no_changes_does_not_create_outbox(self, integration_db, mock_user):
        """
        GIVEN: An existing activity exclusion
        WHEN: update_centre_activity_exclusion is called with no actual changes
        THEN: No new OutboxEvent is created for ACTIVITY_EXCLUSION_UPDATED
        NOTE: This function will create one extra record in the CentreActivityExclusion table, and no record in Outbox table.
        
        Goal: This function checks if updating an activity exclusion with no actual changes does NOT create an outbox event.
        """
        # Create exclusion
        exclusion_data = CentreActivityExclusionCreate(
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="Test No Changes",
            start_date=date.today(),
            end_date=None
        )
        exclusion = create_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=exclusion_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity Exclusion ID: {exclusion.id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(exclusion.id)
        ).delete()
        integration_db.commit()
        
        # "Update" with same values (no actual changes)
        update_data = CentreActivityExclusionUpdate(
            id=exclusion.id,
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="Test No Changes",
            start_date=date.today(),
            end_date=None,
            is_deleted=False,
            modified_by_id="test-user-1"
        )
        update_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: No-change update processed")
        
        # No new ACTIVITY_EXCLUSION_UPDATED event should be created
        updated_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_EXCLUSION_UPDATED",
            OutboxEvent.aggregate_id == str(exclusion.id)
        ).first()
        
        assert updated_event is None
        print(f"DONE: Verified no UPDATE event created")

class TestActivityExclusionDeleteOutbox:    
    def test_delete_exclusion_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing activity exclusion
        WHEN: delete_centre_activity_exclusion is called
        THEN: OutboxEvent records deletion atomically
        
        Goal: This function checks if soft-deleting an activity exclusion creates an outbox event with the deletion info.
        """
        # Create exclusion
        exclusion_data = CentreActivityExclusionCreate(
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="To Delete",
            start_date=date.today(),
            end_date=None
        )
        exclusion = create_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=exclusion_data,
            current_user_info=mock_user
        )
        original_id = exclusion.id
        
        print(f"\nDONE: Created Activity Exclusion ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Delete exclusion
        deleted_exclusion = delete_centre_activity_exclusion(
            db=integration_db,
            exclusion_id=original_id,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Activity Exclusion ID: {original_id}")
        
        # Assertions: Exclusion soft-deleted
        assert deleted_exclusion.is_deleted == True
        refreshed = get_centre_activity_exclusion_by_id(
            db=integration_db,
            exclusion_id=original_id,
            include_deleted=True
        )
        assert refreshed.is_deleted == True
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_EXCLUSION_DELETED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.centre_activity_exclusion.deleted.{original_id}"
        
        print(f"DONE: Created DELETE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload
        payload = outbox_event.get_payload()
        assert payload["deleted_by"] == "test-user-1"
        assert "exclusion_data" in payload

class TestOutboxTransactionAtomicity:
    """Test that activity exclusion and outbox events are created atomically"""
    
    def test_exclusion_and_outbox_created_together_or_not_at_all(self, integration_db, mock_user):
        """
        GIVEN: Create operation succeeds
        WHEN: Transaction is committed
        THEN: Both exclusion and outbox event exist
        
        Goal: This function checks if the creation of activity exclusion and outbox event are atomic - both created or neither.
        """
        initial_exclusion_count = integration_db.query(CentreActivityExclusion).count()
        initial_outbox_count = integration_db.query(OutboxEvent).count()
        
        exclusion_data = CentreActivityExclusionCreate(
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="Atomic Test",
            start_date=date.today(),
            end_date=None
        )
        
        exclusion = create_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=exclusion_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity Exclusion ID: {exclusion.id}")
        
        final_exclusion_count = integration_db.query(CentreActivityExclusion).count()
        final_outbox_count = integration_db.query(OutboxEvent).count()
        
        # Both should be created together
        assert final_exclusion_count == initial_exclusion_count + 1
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Exclusion count: {initial_exclusion_count} → {final_exclusion_count}")
        print(f"DONE: Outbox count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify they reference the same aggregate
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(exclusion.id)
        ).first()
        assert outbox is not None
        
        print(f"DONE: Verified atomic creation")

    def test_exclusion_update_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing activity exclusion that will be updated
        WHEN: Update operation succeeds
        THEN: Exclusion modification and outbox event creation occur atomically
        
        Goal: This function checks if updating an activity exclusion creates an outbox event with the same data.
        """
        # Create initial exclusion
        exclusion_data = CentreActivityExclusionCreate(
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="Atomic Update Test",
            start_date=date.today(),
            end_date=None
        )
        exclusion = create_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=exclusion_data,
            current_user_info=mock_user
        )
        original_id = exclusion.id
        original_modified_date = exclusion.modified_date
        
        print(f"\nDONE: Created Activity Exclusion ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_EXCLUSION_UPDATED"
        ).count()
        
        # Update exclusion
        update_data = CentreActivityExclusionUpdate(
            id=original_id,
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="Atomically Updated Remarks",
            start_date=date.today(),
            end_date=None,
            is_deleted=False,
            modified_by_id="test-user-1"
        )
        updated_exclusion = update_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Activity Exclusion ID: {original_id}")
        
        # Verify exclusion was actually modified in the database
        refreshed_exclusion = get_centre_activity_exclusion_by_id(
            db=integration_db,
            exclusion_id=original_id,
            include_deleted=False
        )
        assert refreshed_exclusion.exclusion_remarks == "Atomically Updated Remarks"
        assert refreshed_exclusion.modified_date > original_modified_date
        assert refreshed_exclusion.modified_by_id == "test-user-1"
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_EXCLUSION_UPDATED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Exclusion modified and Outbox UPDATED count: {initial_outbox_count} -> {final_outbox_count}")
        
        # Verify the outbox event references the updated exclusion
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "ACTIVITY_EXCLUSION_UPDATED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.centre_activity_exclusion.updated.{original_id}"
        
        print(f"DONE: Verified atomic update - exclusion modified and outbox event created together")

    def test_exclusion_delete_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing activity exclusion that will be deleted
        WHEN: Delete operation succeeds
        THEN: Exclusion soft-deletion and outbox event creation occur atomically
        
        Goal: This function checks if soft-deleting an activity exclusion creates an outbox event with the same deletion info.
        """
        # Create initial exclusion
        exclusion_data = CentreActivityExclusionCreate(
            centre_activity_id=1,
            patient_id=1,
            exclusion_remarks="Atomic Delete Test",
            start_date=date.today(),
            end_date=None
        )
        exclusion = create_centre_activity_exclusion(
            db=integration_db,
            exclusion_data=exclusion_data,
            current_user_info=mock_user
        )
        original_id = exclusion.id
        original_modified_date = exclusion.modified_date
        
        print(f"\nDONE: Created Activity Exclusion ID: {original_id}")
        
        # Verify exclusion is not deleted initially
        assert exclusion.is_deleted == False
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_EXCLUSION_DELETED"
        ).count()
        
        # Delete exclusion (soft delete)
        deleted_exclusion = delete_centre_activity_exclusion(
            db=integration_db,
            exclusion_id=original_id,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Activity Exclusion ID: {original_id}")
        
        # Verify exclusion was soft-deleted in the database
        refreshed_exclusion = get_centre_activity_exclusion_by_id(
            db=integration_db,
            exclusion_id=original_id,
            include_deleted=True
        )
        assert refreshed_exclusion is not None
        assert refreshed_exclusion.is_deleted == True
        assert refreshed_exclusion.modified_date > original_modified_date
        assert refreshed_exclusion.modified_by_id == "test-user-1"
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_EXCLUSION_DELETED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Exclusion soft-deleted and Outbox DELETED count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify the outbox event references the deleted exclusion
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "ACTIVITY_EXCLUSION_DELETED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.centre_activity_exclusion.deleted.{original_id}"
        
        # Verify payload contains deletion information
        payload = outbox.get_payload()
        assert payload["exclusion_id"] == original_id
        assert payload["deleted_by"] == "test-user-1"
        assert "exclusion_data" in payload
        
        print(f"DONE: Verified atomic deletion - exclusion soft-deleted and outbox event created together")
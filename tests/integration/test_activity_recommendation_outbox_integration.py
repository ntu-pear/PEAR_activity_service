"""
Integration tests for Activity Recommendation Service (Publisher) Outbox Pattern
Tests the flow: Activity Recommendation CRUD -> OUTBOX_EVENTS table creation

Run Pytest with command: 
1. Run everything: pytest tests/integration/test_activity_recommendation_outbox_integration.py -v -s
2. Run specific test class: pytest tests/integration/test_activity_recommendation_outbox_integration.py::TestActivityRecommendationCreateOutbox -v -s
3. Run specific test function: pytest tests/integration/test_activity_recommendation_outbox_integration.py::TestActivityRecommendationCreateOutbox::test_create_recommendation_creates_outbox_event -v -s

"""

import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.crud.centre_activity_recommendation_crud import (
    create_centre_activity_recommendation,
    delete_centre_activity_recommendation,
    get_centre_activity_recommendation_by_id,
    update_centre_activity_recommendation,
)
from app.database import SessionLocal
from app.models.centre_activity_recommendation_model import CentreActivityRecommendation
from app.models.outbox_model import OutboxEvent
from app.schemas.centre_activity_recommendation_schema import (
    CentreActivityRecommendationCreate,
    CentreActivityRecommendationUpdate,
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
        # "id": "test-doctor-1",
        "id": "test-doctor-1",
        "fullname": "Integration Test User Doctor",
        "role_name": "DOCTOR",
        "bearer_token": "test-token-123"
    }
    
class TestActivityRecommendationCreateOutbox:    
    def test_create_recommendation_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: Activity Recommendation data
        WHEN: create_centre_activity_recommendation is called
        THEN: CentreActivityRecommendation and OutboxEvent are created atomically
        
        Goal: Check if the creation of activity recommendation also creates an outbox event. This function checks if the created records are the same
        
        """
        recommendation_data = CentreActivityRecommendationCreate(
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=1,
            doctor_remarks="Recommended for patient recovery",
            created_by_id="test-doctor-1"
        )
        
        # Create activity recommendation
        recommendation = create_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=recommendation_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity Recommendation ID: {recommendation.id}")
        print(f"  Centre Activity ID: {recommendation.centre_activity_id}")
        print(f"  Patient ID: {recommendation.patient_id}")
        print(f"  Doctor Recommendation: {recommendation.doctor_recommendation}")
        print(f"  Created By: {recommendation.created_by_id}")
        
        # Assertions: Recommendation created
        assert recommendation.id is not None
        assert recommendation.centre_activity_id == 1
        assert recommendation.patient_id == 1
        assert recommendation.doctor_recommendation == 1
        assert recommendation.created_by_id == "test-doctor-1"
        assert recommendation.is_deleted == False
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(recommendation.id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.event_type == "ACTIVITY_RECOMMENDATION_CREATED"
        assert outbox_event.aggregate_id == str(recommendation.id)
        assert outbox_event.routing_key == f"activity.recommendation.created.{recommendation.id}"
        
        print(f"DONE: Created Outbox Event ID: {outbox_event.id}")
        print(f"  Event Type: {outbox_event.event_type}")
        print(f"  Correlation ID: {outbox_event.correlation_id}")
        
        # Verify payload structure
        payload = outbox_event.get_payload()
        assert payload["event_type"] == "ACTIVITY_RECOMMENDATION_CREATED"
        assert payload["recommendation_id"] == recommendation.id
        assert payload["created_by"] == "test-doctor-1"
        assert "correlation_id" in payload
        assert "timestamp" in payload

class TestActivityRecommendationUpdateOutbox:    
    def test_update_recommendation_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing activity recommendation
        WHEN: update_centre_activity_recommendation is called with changes
        THEN: OutboxEvent records changes atomically
        
        Goal: This function checks if updating an activity recommendation creates an outbox event with the changes.
        """
        # Create initial recommendation
        recommendation_data = CentreActivityRecommendationCreate(
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=0,
            doctor_remarks="Original remarks",
            created_by_id="test-doctor-1"
        )
        recommendation = create_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=recommendation_data,
            current_user_info=mock_user
        )
        original_id = recommendation.id
        
        print(f"\nDONE: Created Activity Recommendation ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Update recommendation
        update_data = CentreActivityRecommendationUpdate(
            id=original_id,
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=1,  # Changed from 0 to 1
            doctor_remarks="Updated remarks - now recommended",
            is_deleted=False,
            modified_by_id="test-doctor-1",
            modified_date=datetime.now()
        )
        updated_recommendation = update_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Activity Recommendation ID: {original_id}")
        
        # Assertions: Recommendation updated
        assert updated_recommendation.doctor_recommendation == 1
        assert updated_recommendation.doctor_remarks == "Updated remarks - now recommended"
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_RECOMMENDATION_UPDATED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.recommendation.updated.{original_id}"
        
        print(f"DONE: Created UPDATE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload contains changes
        payload = outbox_event.get_payload()
        assert "changes" in payload
        assert "doctor_recommendation" in payload["changes"]
        assert payload["changes"]["doctor_recommendation"]["old"] == 0
        assert payload["changes"]["doctor_recommendation"]["new"] == 1
        assert "doctor_remarks" in payload["changes"]
    
    def test_update_with_no_changes_does_not_create_outbox(self, integration_db, mock_user):
        """
        GIVEN: An existing activity recommendation
        WHEN: update_centre_activity_recommendation is called with no actual changes
        THEN: No new OutboxEvent is created for ACTIVITY_RECOMMENDATION_UPDATED
        NOTE: This function will create one extra record in the CentreActivityRecommendation table, and no record in Outbox table.
        
        Goal: This function checks if updating an activity recommendation with no actual changes does NOT create an outbox event.
        """
        # Create recommendation
        recommendation_data = CentreActivityRecommendationCreate(
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=0,
            doctor_remarks="Test No Changes",
            created_by_id="test-doctor-1"
        )
        recommendation = create_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=recommendation_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity Recommendation ID: {recommendation.id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(recommendation.id)
        ).delete()
        integration_db.commit()
        
        # "Update" with same values (no actual changes)
        update_data = CentreActivityRecommendationUpdate(
            id=recommendation.id,
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=0,
            doctor_remarks="Test No Changes",
            is_deleted=False,
            modified_by_id="test-doctor-1",
            modified_date=datetime.now()
        )
        update_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: No-change update processed")
        
        # No new ACTIVITY_RECOMMENDATION_UPDATED event should be created
        updated_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_RECOMMENDATION_UPDATED",
            OutboxEvent.aggregate_id == str(recommendation.id)
        ).first()
        
        assert updated_event is None
        print(f"DONE: Verified no UPDATE event created")

class TestActivityRecommendationDeleteOutbox:    
    def test_delete_recommendation_creates_outbox_event(self, integration_db, mock_user):
        """
        GIVEN: An existing activity recommendation
        WHEN: delete_centre_activity_recommendation is called
        THEN: OutboxEvent records deletion atomically
        
        Goal: This function checks if soft-deleting an activity recommendation creates an outbox event with the deletion info.
        """
        # Create recommendation
        recommendation_data = CentreActivityRecommendationCreate(
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=1,
            doctor_remarks="To Delete",
            created_by_id="test-doctor-1"
        )
        recommendation = create_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=recommendation_data,
            current_user_info=mock_user
        )
        original_id = recommendation.id
        
        print(f"\nDONE: Created Activity Recommendation ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Delete recommendation
        deleted_recommendation = delete_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_id=original_id,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Activity Recommendation ID: {original_id}")
        
        # Assertions: Recommendation soft-deleted
        assert deleted_recommendation.is_deleted == True
        refreshed = get_centre_activity_recommendation_by_id(
            db=integration_db,
            centre_activity_recommendation_id=original_id,
            include_deleted=True
        )
        assert refreshed.is_deleted == True
        
        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_RECOMMENDATION_DELETED",
            OutboxEvent.aggregate_id == str(original_id)
        ).first()
        
        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.recommendation.deleted.{original_id}"
        
        print(f"DONE: Created DELETE Outbox Event ID: {outbox_event.id}")
        
        # Verify payload
        payload = outbox_event.get_payload()
        assert payload["deleted_by"] == "test-doctor-1"
        assert "recommendation_data" in payload

class TestOutboxTransactionAtomicity:
    """Test that activity recommendation and outbox events are created atomically"""
    
    def test_recommendation_and_outbox_created_together_or_not_at_all(self, integration_db, mock_user):
        """
        GIVEN: Create operation succeeds
        WHEN: Transaction is committed
        THEN: Both recommendation and outbox event exist
        
        Goal: This function checks if the creation of activity recommendation and outbox event are atomic - both created or neither.
        """
        initial_recommendation_count = integration_db.query(CentreActivityRecommendation).count()
        initial_outbox_count = integration_db.query(OutboxEvent).count()
        
        recommendation_data = CentreActivityRecommendationCreate(
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=1,
            doctor_remarks="Atomic Test",
            created_by_id="test-doctor-1"
        )
        
        recommendation = create_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=recommendation_data,
            current_user_info=mock_user
        )
        
        print(f"\nDONE: Created Activity Recommendation ID: {recommendation.id}")
        
        final_recommendation_count = integration_db.query(CentreActivityRecommendation).count()
        final_outbox_count = integration_db.query(OutboxEvent).count()
        
        # Both should be created together
        assert final_recommendation_count == initial_recommendation_count + 1
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Recommendation count: {initial_recommendation_count} → {final_recommendation_count}")
        print(f"DONE: Outbox count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify they reference the same aggregate
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(recommendation.id)
        ).first()
        assert outbox is not None
        
        print(f"DONE: Verified atomic creation")

    def test_recommendation_update_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing activity recommendation that will be updated
        WHEN: Update operation succeeds
        THEN: Recommendation modification and outbox event creation occur atomically
        
        Goal: This function checks if updating an activity recommendation creates an outbox event with the same data.
        """
        # Create initial recommendation
        recommendation_data = CentreActivityRecommendationCreate(
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=-1,
            doctor_remarks="Atomic Update Test",
            created_by_id="test-doctor-1"
        )
        recommendation = create_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=recommendation_data,
            current_user_info=mock_user
        )
        original_id = recommendation.id
        original_modified_date = recommendation.modified_date
        
        print(f"\nDONE: Created Activity Recommendation ID: {original_id}")
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_RECOMMENDATION_UPDATED"
        ).count()
        
        # Update recommendation
        update_data = CentreActivityRecommendationUpdate(
            id=original_id,
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=1,  # Changed from -1 to 1
            doctor_remarks="Atomically Updated Remarks",
            is_deleted=False,
            modified_by_id="test-doctor-1",
            modified_date=datetime.now()
        )
        updated_recommendation = update_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=update_data,
            current_user_info=mock_user
        )
        
        print(f"DONE: Updated Activity Recommendation ID: {original_id}")
        
        # Verify recommendation was actually modified in the database
        refreshed_recommendation = get_centre_activity_recommendation_by_id(
            db=integration_db,
            centre_activity_recommendation_id=original_id,
            include_deleted=False
        )
        assert refreshed_recommendation.doctor_recommendation == 1
        assert refreshed_recommendation.doctor_remarks == "Atomically Updated Remarks"
        assert refreshed_recommendation.modified_date > original_modified_date
        assert refreshed_recommendation.modified_by_id == "test-doctor-1"
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_RECOMMENDATION_UPDATED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Recommendation modified and Outbox UPDATED count: {initial_outbox_count} -> {final_outbox_count}")
        
        # Verify the outbox event references the updated recommendation
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "ACTIVITY_RECOMMENDATION_UPDATED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.recommendation.updated.{original_id}"
        
        print(f"DONE: Verified atomic update - recommendation modified and outbox event created together")

    def test_recommendation_delete_and_outbox_created_atomically(self, integration_db, mock_user):
        """
        GIVEN: An existing activity recommendation that will be deleted
        WHEN: Delete operation succeeds
        THEN: Recommendation soft-deletion and outbox event creation occur atomically
        
        Goal: This function checks if soft-deleting an activity recommendation creates an outbox event with the same deletion info.
        """
        # Create initial recommendation
        recommendation_data = CentreActivityRecommendationCreate(
            centre_activity_id=1,
            patient_id=1,
            doctor_recommendation=1,
            doctor_remarks="Atomic Delete Test",
            created_by_id="test-doctor-1"
        )
        recommendation = create_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_data=recommendation_data,
            current_user_info=mock_user
        )
        original_id = recommendation.id
        original_modified_date = recommendation.modified_date
        
        print(f"\nDONE: Created Activity Recommendation ID: {original_id}")
        
        # Verify recommendation is not deleted initially
        assert recommendation.is_deleted == False
        
        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id)
        ).delete()
        integration_db.commit()
        
        # Get initial state
        initial_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_RECOMMENDATION_DELETED"
        ).count()
        
        # Delete recommendation (soft delete)
        deleted_recommendation = delete_centre_activity_recommendation(
            db=integration_db,
            centre_activity_recommendation_id=original_id,
            current_user_info=mock_user
        )
        
        print(f"DONE: Deleted Activity Recommendation ID: {original_id}")
        
        # Verify recommendation was soft-deleted in the database
        refreshed_recommendation = get_centre_activity_recommendation_by_id(
            db=integration_db,
            centre_activity_recommendation_id=original_id,
            include_deleted=True
        )
        assert refreshed_recommendation is not None
        assert refreshed_recommendation.is_deleted == True
        assert refreshed_recommendation.modified_date > original_modified_date
        assert refreshed_recommendation.modified_by_id == "test-doctor-1"
        
        # Verify outbox event was created in the same transaction
        final_outbox_count = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ACTIVITY_RECOMMENDATION_DELETED"
        ).count()
        assert final_outbox_count == initial_outbox_count + 1
        
        print(f"DONE: Recommendation soft-deleted and Outbox DELETED count: {initial_outbox_count} → {final_outbox_count}")
        
        # Verify the outbox event references the deleted recommendation
        outbox = integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(original_id),
            OutboxEvent.event_type == "ACTIVITY_RECOMMENDATION_DELETED"
        ).first()
        assert outbox is not None
        assert outbox.routing_key == f"activity.recommendation.deleted.{original_id}"
        
        # Verify payload contains deletion information
        payload = outbox.get_payload()
        assert payload["recommendation_id"] == original_id
        assert payload["deleted_by"] == "test-doctor-1"
        assert "recommendation_data" in payload
        
        print(f"DONE: Verified atomic deletion - recommendation soft-deleted and outbox event created together")
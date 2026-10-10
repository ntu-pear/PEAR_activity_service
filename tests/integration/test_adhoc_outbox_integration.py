"""
Integration tests for Adhoc (Publisher) Outbox Pattern
Tests the flow: Adhoc CRUD -> OUTBOX_EVENTS table creation

Run Pytest with command:
1. Run everything: pytest tests/integration/test_adhoc_outbox_integration.py -v -s
2. Run specific test class: pytest tests/integration/test_adhoc_outbox_integration.py::TestAdhocCreateOutbox -v -s
3. Run specific test function: pytest tests/integration/test_adhoc_outbox_integration.py::TestAdhocCreateOutbox::test_create_adhoc_creates_outbox_event -v -s

"""

from datetime import date, datetime, time

import pytest
from fastapi import HTTPException

from app.crud.adhoc_crud import create_adhoc, delete_adhoc, get_adhoc_by_id, update_adhoc
from app.crud.centre_activity_crud import create_centre_activity
from app.models.adhoc_model import Adhoc
from app.models.outbox_model import OutboxEvent
from app.schemas.adhoc_schema import AdhocCreate, AdhocUpdate
from app.schemas.centre_activity_schema import CentreActivityCreate

# Fields the scheduler's `adhoc_service_to_scheduler` mapper reads off the payload.
# Keep in sync with PEAR_scheduler/messaging/mappers/mapper_util.py
MAPPER_REQUIRED_FIELDS = [
    "id",
    "patient_id",
    "old_centre_activity_id",
    "new_centre_activity_id",
]
MAPPER_OPTIONAL_FIELDS = [
    "start_date",
    "end_date",
    "status",
    "is_deleted",
    "created_date",
    "modified_date",
    "created_by_id",
    "modified_by_id",
]


def _today_at(hour: int) -> datetime:
    """Anchor adhoc dates inside today, which always satisfies the schema validators."""
    return datetime.combine(date.today(), time(hour=hour))


@pytest.fixture
def second_centre_activity(integration_db, mock_user):
    """
    An adhoc needs two DIFFERENT centre activities. The session fixture only
    guarantees CentreActivity ID=1, so create a second, non-duplicate one here.

    Schema constraints this has to satisfy (see ValidatedCentreActivity):
      - min_duration must EQUAL max_duration, and both must be 30 or 60
      - is_group=True requires min_people_req >= 2
      - is_fixed/is_compulsory would require fixed_time_slots, so both stay False
    It also differs from CentreActivity ID=1 on the essential fields, so the
    duplicate check in create_centre_activity does not reject it.
    """
    centre_activity_data = CentreActivityCreate(
        activity_id=1,
        is_compulsory=False,
        is_fixed=False,
        is_group=True,
        start_date=date.today(),
        end_date=date(2999, 12, 31),
        min_duration=30,
        max_duration=30,
        min_people_req=2,
        created_by_id=mock_user["id"],
    )
    return create_centre_activity(
        db=integration_db,
        centre_activity_data=centre_activity_data,
        current_user_info=mock_user,
    )


@pytest.fixture
def adhoc_payload(second_centre_activity, mock_user):
    """Valid AdhocCreate pointing at CentreActivity 1 -> the second centre activity."""
    return AdhocCreate(
        old_centre_activity_id=1,
        new_centre_activity_id=second_centre_activity.id,
        patient_id=1,
        status="PENDING",
        start_date=_today_at(9),
        end_date=_today_at(10),
        created_by_id=mock_user["id"],
    )


class TestAdhocCreateOutbox:
    def test_create_adhoc_creates_outbox_event(self, integration_db, mock_user, adhoc_payload):
        """
        GIVEN: Valid adhoc data
        WHEN: create_adhoc is called
        THEN: Adhoc and OutboxEvent are created atomically

        Goal: Check that creating an adhoc also writes an ADHOC_CREATED outbox event.
        """
        adhoc = create_adhoc(
            db=integration_db,
            adhoc_data=adhoc_payload,
            current_user_info=mock_user,
        )

        print(f"\nDONE: Created Adhoc ID: {adhoc.id}")
        print(f"  Old CentreActivity: {adhoc.old_centre_activity_id}")
        print(f"  New CentreActivity: {adhoc.new_centre_activity_id}")

        # Assertions: Adhoc created
        assert adhoc.id is not None
        assert adhoc.status == "PENDING"
        assert adhoc.is_deleted == False

        # Assertions: Outbox event created.
        # Filter on event_type too - the centre activity fixture writes its own
        # outbox row, and the two tables have independent identity sequences,
        # so aggregate_id alone is not unique across event types.
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ADHOC_CREATED",
            OutboxEvent.aggregate_id == str(adhoc.id),
        ).first()

        assert outbox_event is not None
        assert outbox_event.event_type == "ADHOC_CREATED"
        assert outbox_event.aggregate_id == str(adhoc.id)
        assert outbox_event.routing_key == f"activity.adhoc.created.{adhoc.id}"

        print(f"DONE: Created Outbox Event ID: {outbox_event.id}")
        print(f"  Correlation ID: {outbox_event.correlation_id}")

        # Verify payload structure - these keys are what the scheduler consumer reads
        payload = outbox_event.get_payload()
        assert payload["event_type"] == "ADHOC_CREATED"
        assert payload["adhoc_id"] == adhoc.id
        assert payload["created_by"] == mock_user["id"]
        assert "correlation_id" in payload
        assert "timestamp" in payload
        assert "adhoc_data" in payload

    def test_create_adhoc_accepts_supplied_correlation_id(self, integration_db, mock_user, adhoc_payload):
        """
        GIVEN: A caller-supplied correlation ID
        WHEN: create_adhoc is called with it
        THEN: The outbox event carries that exact correlation ID

        Goal: Check the correlation ID is threaded through rather than regenerated.
        """
        supplied = "ADHOC-TEST-CORRELATION-0001"

        adhoc = create_adhoc(
            db=integration_db,
            adhoc_data=adhoc_payload,
            current_user_info=mock_user,
            correlation_id=supplied,
        )

        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ADHOC_CREATED",
            OutboxEvent.aggregate_id == str(adhoc.id),
        ).first()

        assert outbox_event is not None
        assert outbox_event.correlation_id == supplied
        assert outbox_event.get_payload()["correlation_id"] == supplied

        print(f"\nDONE: Correlation ID passed through: {supplied}")

    def test_create_adhoc_with_unknown_centre_activity_creates_no_outbox(
        self, integration_db, mock_user, second_centre_activity
    ):
        """
        GIVEN: An adhoc referencing a non-existent centre activity
        WHEN: create_adhoc is called
        THEN: HTTPException raised and no outbox event created

        Goal: Check a rejected create leaves no event behind.
        """
        initial_outbox_count = integration_db.query(OutboxEvent).count()

        bad_payload = AdhocCreate(
            old_centre_activity_id=99999,
            new_centre_activity_id=second_centre_activity.id,
            patient_id=1,
            status="PENDING",
            start_date=_today_at(9),
            end_date=_today_at(10),
            created_by_id=mock_user["id"],
        )

        with pytest.raises(HTTPException) as exc_info:
            create_adhoc(
                db=integration_db,
                adhoc_data=bad_payload,
                current_user_info=mock_user,
            )

        assert exc_info.value.status_code == 404

        print(f"\nDONE: Adhoc with unknown centre activity properly rejected")

        final_outbox_count = integration_db.query(OutboxEvent).count()
        assert final_outbox_count == initial_outbox_count


class TestAdhocUpdateOutbox:
    def test_update_adhoc_creates_outbox_event(self, integration_db, mock_user, adhoc_payload):
        """
        GIVEN: An existing adhoc
        WHEN: update_adhoc is called with changes
        THEN: An ADHOC_UPDATED OutboxEvent records the changes atomically

        Goal: Check updating an adhoc emits an event carrying the new state and the diff.
        """
        adhoc = create_adhoc(
            db=integration_db,
            adhoc_data=adhoc_payload,
            current_user_info=mock_user,
        )
        adhoc_id = adhoc.id

        print(f"\nDONE: Created Adhoc ID: {adhoc_id}")

        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(adhoc_id)
        ).delete()
        integration_db.commit()

        update_data = AdhocUpdate(
            id=adhoc_id,
            old_centre_activity_id=adhoc.old_centre_activity_id,
            new_centre_activity_id=adhoc.new_centre_activity_id,
            patient_id=adhoc.patient_id,
            status="APPROVED",
            start_date=_today_at(9),
            end_date=_today_at(10),
            is_deleted=False,
            modified_by_id=mock_user["id"],
        )
        updated_adhoc = update_adhoc(
            db=integration_db,
            adhoc_data=update_data,
            current_user_info=mock_user,
        )

        print(f"DONE: Updated Adhoc ID: {adhoc_id}")

        # Assertions: Adhoc updated
        assert updated_adhoc.status == "APPROVED"
        assert updated_adhoc.modified_by_id == mock_user["id"]

        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ADHOC_UPDATED",
            OutboxEvent.aggregate_id == str(adhoc_id),
        ).first()

        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.adhoc.updated.{adhoc_id}"

        print(f"DONE: Created UPDATE Outbox Event ID: {outbox_event.id}")

        # Verify payload carries new state, prior state and the diff
        payload = outbox_event.get_payload()
        assert payload["adhoc_id"] == adhoc_id
        assert payload["modified_by"] == mock_user["id"]
        assert payload["adhoc_data"]["status"] == "APPROVED"
        assert payload["old_data"]["status"] == "PENDING"
        assert "changes" in payload
        assert payload["changes"]["status"]["old"] == "PENDING"
        assert payload["changes"]["status"]["new"] == "APPROVED"

    def test_update_nonexistent_adhoc_fails(self, integration_db, mock_user, second_centre_activity):
        """
        GIVEN: Non-existent adhoc ID
        WHEN: update_adhoc is called
        THEN: HTTPException raised and no outbox event created

        Goal: Check updating a missing adhoc is rejected and emits nothing.
        """
        initial_outbox_count = integration_db.query(OutboxEvent).count()

        update_data = AdhocUpdate(
            id=99999,
            old_centre_activity_id=1,
            new_centre_activity_id=second_centre_activity.id,
            patient_id=1,
            status="APPROVED",
            start_date=_today_at(9),
            end_date=_today_at(10),
            is_deleted=False,
            modified_by_id=mock_user["id"],
        )

        with pytest.raises(HTTPException) as exc_info:
            update_adhoc(
                db=integration_db,
                adhoc_data=update_data,
                current_user_info=mock_user,
            )

        assert exc_info.value.status_code == 404

        print(f"\nDONE: Update of non-existent adhoc properly rejected")

        final_outbox_count = integration_db.query(OutboxEvent).count()
        assert final_outbox_count == initial_outbox_count


class TestAdhocDeleteOutbox:
    def test_delete_adhoc_creates_outbox_event(self, integration_db, mock_user, adhoc_payload):
        """
        GIVEN: An existing adhoc
        WHEN: delete_adhoc is called
        THEN: An ADHOC_DELETED OutboxEvent records the soft delete atomically

        Goal: Check soft-deleting an adhoc emits an event the scheduler can act on.
        """
        adhoc = create_adhoc(
            db=integration_db,
            adhoc_data=adhoc_payload,
            current_user_info=mock_user,
        )
        adhoc_id = adhoc.id

        print(f"\nDONE: Created Adhoc ID: {adhoc_id}")

        # Clear outbox from creation
        integration_db.query(OutboxEvent).filter(
            OutboxEvent.aggregate_id == str(adhoc_id)
        ).delete()
        integration_db.commit()

        deleted_adhoc = delete_adhoc(
            db=integration_db,
            adhoc_id=adhoc_id,
            current_user_info=mock_user,
        )

        print(f"DONE: Deleted Adhoc ID: {adhoc_id}")

        # Assertions: Adhoc soft-deleted
        assert deleted_adhoc.is_deleted == True
        refreshed = get_adhoc_by_id(
            db=integration_db,
            adhoc_id=adhoc_id,
            include_deleted=True,
        )
        assert refreshed.is_deleted == True

        # Assertions: Outbox event created
        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ADHOC_DELETED",
            OutboxEvent.aggregate_id == str(adhoc_id),
        ).first()

        assert outbox_event is not None
        assert outbox_event.routing_key == f"activity.adhoc.deleted.{adhoc_id}"

        print(f"DONE: Created DELETE Outbox Event ID: {outbox_event.id}")

        # The scheduler's delete handler reads message_data["timestamp"] unguarded
        payload = outbox_event.get_payload()
        assert payload["deleted_by"] == mock_user["id"]
        assert "adhoc_data" in payload
        assert payload["timestamp"]
        assert payload["adhoc_data"]["is_deleted"] == True

    def test_delete_nonexistent_adhoc_fails(self, integration_db, mock_user):
        """
        GIVEN: Non-existent adhoc ID
        WHEN: delete_adhoc is called
        THEN: HTTPException raised and no outbox event created

        Goal: Check deleting a missing adhoc is rejected and emits nothing.
        """
        initial_outbox_count = integration_db.query(OutboxEvent).count()

        with pytest.raises(HTTPException) as exc_info:
            delete_adhoc(
                db=integration_db,
                adhoc_id=99999,
                current_user_info=mock_user,
            )

        assert exc_info.value.status_code == 404

        print(f"\nDONE: Delete of non-existent adhoc properly rejected")

        final_outbox_count = integration_db.query(OutboxEvent).count()
        assert final_outbox_count == initial_outbox_count


class TestAdhocPayloadContract:
    """The payload must stay compatible with the scheduler's adhoc mapper."""

    def test_adhoc_data_carries_every_mapped_field(self, integration_db, mock_user, adhoc_payload):
        """
        GIVEN: An adhoc create
        WHEN: The outbox payload is inspected
        THEN: adhoc_data contains every field the scheduler mapper maps

        Goal: Catch column renames that would silently break the scheduler mapping.
        """
        adhoc = create_adhoc(
            db=integration_db,
            adhoc_data=adhoc_payload,
            current_user_info=mock_user,
        )

        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ADHOC_CREATED",
            OutboxEvent.aggregate_id == str(adhoc.id),
        ).first()
        assert outbox_event is not None
        payload = outbox_event.get_payload()
        adhoc_data = payload["adhoc_data"]

        for field in MAPPER_REQUIRED_FIELDS:
            assert field in adhoc_data, f"Mapper required field missing: {field}"
            assert adhoc_data[field] is not None, f"Mapper required field is None: {field}"

        for field in MAPPER_OPTIONAL_FIELDS:
            assert field in adhoc_data, f"Mapper field missing: {field}"

        print(f"\nDONE: adhoc_data carries all {len(MAPPER_REQUIRED_FIELDS) + len(MAPPER_OPTIONAL_FIELDS)} mapped fields")

    def test_adhoc_data_excludes_orm_relationships(self, integration_db, mock_user, adhoc_payload):
        """
        GIVEN: A delete, which touches the centre activity relationships for logging
        WHEN: The outbox payload is inspected
        THEN: No ORM relationship object leaked into adhoc_data

        Goal: Guard against lazy-loaded relationships being swept into the message.
        """
        adhoc = create_adhoc(
            db=integration_db,
            adhoc_data=adhoc_payload,
            current_user_info=mock_user,
        )

        delete_adhoc(
            db=integration_db,
            adhoc_id=adhoc.id,
            current_user_info=mock_user,
        )

        outbox_event = integration_db.query(OutboxEvent).filter(
            OutboxEvent.event_type == "ADHOC_DELETED",
            OutboxEvent.aggregate_id == str(adhoc.id),
        ).first()
        adhoc_data = outbox_event.get_payload()["adhoc_data"]

        assert "old_centre_activity" not in adhoc_data
        assert "new_centre_activity" not in adhoc_data

        expected_columns = set(Adhoc.__table__.columns.keys())
        # Titles are the only enrichment allowed on top of the mapped columns
        extra = set(adhoc_data) - expected_columns - {"old_activity_title", "new_activity_title"}
        assert not extra, f"Unexpected keys leaked into payload: {extra}"

        print(f"\nDONE: Payload contains only mapped columns plus activity titles")

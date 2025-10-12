import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import uuid


from app.messaging.activity_exclusion_publisher import ActivityExclusionPublisher, get_activity_exclusion_publisher


@pytest.fixture
def mock_producer_manager():
    """Fixture for mocked producer manager"""
    with patch('app.messaging.activity_exclusion_publisher.get_producer_manager') as mock:
        manager = MagicMock()
        manager.declare_exchange.return_value = None
        manager.publish.return_value = True
        mock.return_value = manager
        yield manager

@pytest.fixture
def sample_exclusion_data():
    """Sample exclusion data for testing."""
    return {
        'start_date': '2025-01-01',
        'end_date': '2025-12-31',
        'exclusion_remarks': 'Patient cannot participate'
    }


def test_init_success(mock_producer_manager):
    """Should initialize with exchange declaration"""
    publisher = ActivityExclusionPublisher(testing=True)

    assert publisher.exchange == 'activity.updates'
    assert publisher.testing is True
    assert publisher.manager is mock_producer_manager
    mock_producer_manager.declare_exchange.assert_called_once_with('activity.updates', 'topic') 

def test_init_exchange_declaration_failure(mock_producer_manager):
    """Should handle exchange declaration failure"""
    mock_producer_manager.declare_exchange.side_effect = Exception("Exchange error")

    publisher = ActivityExclusionPublisher(testing=True)

    assert publisher.exchange == 'activity.updates'
    assert publisher.manager is mock_producer_manager
    mock_producer_manager.declare_exchange.assert_called_once_with('activity.updates', 'topic')

# ==== publish_exclusion_created tests ====
@patch('app.messaging.activity_exclusion_publisher.datetime')
@patch('app.messaging.activity_exclusion_publisher.uuid.uuid4')
def test_publish_exclusion_created_success(mock_uuid, mock_datetime, mock_producer_manager, sample_exclusion_data):
    """Should publish exclusion created message successfully"""
    # setup mocks
    mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
    fixed_datetime = datetime(2025, 1, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_datetime

    publisher = ActivityExclusionPublisher(testing=True)

    result = publisher.publish_exclusion_created(
        exclusion_id = 1,
        patient_id = 100,
        centre_activity_id = 200,
        exclusion_data = sample_exclusion_data,
        created_by="user1"
    )

    assert result is True

    expected_message = {
        'correlation_id': '12345678-1234-5678-1234-567812345678',
        'event_type': 'ACTIVITY_EXCLUSION_CREATED',
        'exclusion_id': 1,
        'patient_id': 100,
        'centre_activity_id': 200,
        'exclusion_data': sample_exclusion_data,
        'created_by': 'user1',
        'timestamp': '2025-01-01T12:00:00'  # ISO format
    }
    mock_producer_manager.publish.assert_called_once_with(
        'activity.updates',
        'activity.centre_activity_exclusion.created.1',
        expected_message
    )

def test_publish_exclusion_created_failure(mock_producer_manager, sample_exclusion_data):
    """Should return False when publish fails"""
    mock_producer_manager.publish.return_value = False

    publisher = ActivityExclusionPublisher(testing=True)

    result = publisher.publish_exclusion_created(
        exclusion_id = 1,
        patient_id = 100,
        centre_activity_id = 200,
        exclusion_data = sample_exclusion_data,
        created_by="user1"
    )

    assert result is False
    mock_producer_manager.publish.assert_called_once()


# ==== publish_exclusion_updated tests ====
@patch('app.messaging.activity_exclusion_publisher.datetime')
@patch('app.messaging.activity_exclusion_publisher.uuid.uuid4')
def test_publish_exclusion_updated_success(mock_uuid, mock_datetime, mock_producer_manager, sample_exclusion_data):
    """Should publich exclusion updated message successfully"""
    # setup mocks
    mock_uuid.return_value = uuid.UUID('87654321-4321-8765-4321-876543218765')
    fixed_datetime = datetime(2025, 10, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_datetime

    publisher = ActivityExclusionPublisher(testing=True)

    old_data = sample_exclusion_data
    new_data = {
        'start_date': '2025-02-01',
        'end_date': '2025-11-30',
        'exclusion_remarks': 'Updated notes'
    }
    changes = {
        'start_date': {'old': old_data['start_date'], 'new': new_data['start_date']},
        'end_date': {'old': old_data['end_date'], 'new': new_data['end_date']},
        'exclusion_remarks': {'old': old_data['exclusion_remarks'], 'new': new_data['exclusion_remarks']}
    }

    result = publisher.publish_exclusion_updated(
        exclusion_id=1,
        patient_id=100,
        centre_activity_id=200,
        old_data=old_data,
        new_data=new_data,
        changes=changes,
        modified_by="user2"
    )

    assert result is True

    expected_message = {
        'correlation_id': '87654321-4321-8765-4321-876543218765',
        'event_type': 'ACTIVITY_EXCLUSION_UPDATED',
        'exclusion_id': 1,
        'patient_id': 100,
        'centre_activity_id': 200,
        'old_data': old_data,
        'new_data': new_data,
        'changes': changes,
        'modified_by': 'user2',
        'timestamp': '2025-10-01T12:00:00'  # ISO format
    }

    mock_producer_manager.publish.assert_called_once_with(
        'activity.updates',
        'activity.centre_activity_exclusion.updated.1',
        expected_message
    )

def test_publish_exclusion_updated_failure(mock_producer_manager, sample_exclusion_data):
    """Should return False when publish fails"""
    mock_producer_manager.publish.return_value = False

    publisher = ActivityExclusionPublisher(testing=True)

    result = publisher.publish_exclusion_updated(
        exclusion_id=1,
        patient_id=100,
        centre_activity_id=200,
        old_data={},
        new_data={},
        changes={},
        modified_by="user2"
    )

    assert result is False
    mock_producer_manager.publish.assert_called_once()

# ==== publish_exclusion_deleted tests ====
@patch('app.messaging.activity_exclusion_publisher.datetime')
@patch('app.messaging.activity_exclusion_publisher.uuid.uuid4')
def test_publish_exclusion_deleted_success(mock_uuid, mock_datetime, mock_producer_manager, sample_exclusion_data):
    """Should publish exclusion deleted message successfully"""
    # setup mocks
    mock_uuid.return_value = uuid.UUID('11223344-5566-7788-99aa-bbccddeeff00')
    fixed_datetime = datetime(2025, 5, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_datetime

    publisher = ActivityExclusionPublisher(testing=True)

    result = publisher.publish_exclusion_deleted(
        exclusion_id=1,
        patient_id=100,
        centre_activity_id=200,
        exclusion_data=sample_exclusion_data,
        deleted_by="user3"
    )

    assert result is True

    expected_message = {
        'correlation_id': '11223344-5566-7788-99aa-bbccddeeff00',
        'event_type': 'ACTIVITY_EXCLUSION_DELETED',
        'exclusion_id': 1,
        'patient_id': 100,
        'centre_activity_id': 200,
        'exclusion_data': sample_exclusion_data,
        'deleted_by': 'user3',
        'timestamp': '2025-05-01T12:00:00'  # ISO format
    }

    mock_producer_manager.publish.assert_called_once_with(
        'activity.updates',
        'activity.centre_activity_exclusion.deleted.1',
        expected_message
    )

def test_publish_exclusion_deleted_failure(mock_producer_manager, sample_exclusion_data):
    """Should return False when publish fails"""
    mock_producer_manager.publish.return_value = False

    publisher = ActivityExclusionPublisher(testing=True)

    result = publisher.publish_exclusion_deleted(
        exclusion_id=1,
        patient_id=100,
        centre_activity_id=200,
        exclusion_data=sample_exclusion_data,
        deleted_by="user3"
    )

    assert result is False
    mock_producer_manager.publish.assert_called_once()

# ==== close method test ====
def test_close(mock_producer_manager):
    """Close should be a no-op"""
    publisher = ActivityExclusionPublisher(testing=True)
    publisher.close()  # Should do nothing and not raise

# ==== Singleton instance tests ====
def test_get_activity_exclusion_publisher_singleton(mock_producer_manager):
    """Should return singleton instance on multiple calls"""

    instance1 = get_activity_exclusion_publisher(testing=True)
    instance2 = get_activity_exclusion_publisher(testing=True)

    assert instance1 is instance2
    assert isinstance(instance1, ActivityExclusionPublisher)
    mock_producer_manager.declare_exchange.assert_called_once_with('activity.updates', 'topic')

#  ==== routing key format tests ====
def test_created_routing_key_format(mock_producer_manager, sample_exclusion_data):
    """Should use correct routing key format for created event"""
    publisher = ActivityExclusionPublisher(testing=True)
    publisher.publish_exclusion_created(
        exclusion_id=42,
        patient_id=100,
        centre_activity_id=200,
        exclusion_data=sample_exclusion_data,
        created_by="user1"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    assert args[1] == 'activity.centre_activity_exclusion.created.42'

def test_updated_routing_key_format(mock_producer_manager, sample_exclusion_data):
    """Should use correct routing key format for updated event"""
    publisher = ActivityExclusionPublisher(testing=True)
    publisher.publish_exclusion_updated(
        exclusion_id=43,
        patient_id=100,
        centre_activity_id=200,
        old_data={},
        new_data={},
        changes={},
        modified_by="user2"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    assert args[1] == 'activity.centre_activity_exclusion.updated.43'

def test_deleted_routing_key_format(mock_producer_manager, sample_exclusion_data):
    """Should use correct routing key format for deleted event"""
    publisher = ActivityExclusionPublisher(testing=True)
    publisher.publish_exclusion_deleted(
        exclusion_id=44,
        patient_id=100,
        centre_activity_id=200,
        exclusion_data=sample_exclusion_data,
        deleted_by="user3"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    assert args[1] == 'activity.centre_activity_exclusion.deleted.44'

# === Message content structure tests === #
def test_created_message_structure(mock_producer_manager, sample_exclusion_data):
    """Should construct correct message structure for created event"""
    publisher = ActivityExclusionPublisher(testing=True)
    publisher.publish_exclusion_created(
        exclusion_id=1,
        patient_id=100,
        centre_activity_id=200,
        exclusion_data=sample_exclusion_data,
        created_by="user1"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    message = args[2]
    required_fields = [
        'correlation_id', 'event_type', 'exclusion_id', 'patient_id',
        'centre_activity_id', 'exclusion_data', 'created_by', 'timestamp'
    ]
    
    for field in required_fields:
        assert field in message
    assert message['event_type'] == 'ACTIVITY_EXCLUSION_CREATED'

def test_updated_message_structure(mock_producer_manager, sample_exclusion_data):
    """Should construct correct message structure for updated event"""
    publisher = ActivityExclusionPublisher(testing=True)
    publisher.publish_exclusion_updated(
        exclusion_id=1,
        patient_id=100,
        centre_activity_id=200,
        old_data={},
        new_data={},
        changes={},
        modified_by="user2"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    message = args[2]
    required_fields = [
        'correlation_id', 'event_type', 'exclusion_id', 'patient_id',
        'centre_activity_id', 'old_data', 'new_data', 'changes',
        'modified_by', 'timestamp'
    ]
    
    for field in required_fields:
        assert field in message
    assert message['event_type'] == 'ACTIVITY_EXCLUSION_UPDATED'

def test_deleted_message_structure(mock_producer_manager, sample_exclusion_data):
    """Should construct correct message structure for deleted event"""
    publisher = ActivityExclusionPublisher(testing=True)
    publisher.publish_exclusion_deleted(
        exclusion_id=1,
        patient_id=100,
        centre_activity_id=200,
        exclusion_data=sample_exclusion_data,
        deleted_by="user3"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    message = args[2]
    required_fields = [
        'correlation_id', 'event_type', 'exclusion_id', 'patient_id',
        'centre_activity_id', 'exclusion_data', 'deleted_by', 'timestamp'
    ]
    
    for field in required_fields:
        assert field in message
    assert message['event_type'] == 'ACTIVITY_EXCLUSION_DELETED'
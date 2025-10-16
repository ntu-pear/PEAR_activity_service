import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import uuid


from app.messaging.centre_activity_publisher import CentreActivityPublisher, get_centre_activity_publisher

@pytest.fixture
def mock_producer_manager():
    """Fixture for mocked producer manager"""
    with patch('app.messaging.centre_activity_publisher.get_producer_manager') as mock:
        manager = MagicMock()
        manager.declare_exchange.return_value = None
        manager.publish.return_value = True
        mock.return_value = manager
        yield manager

@pytest.fixture
def sample_centre_activity_data():
    """Sample centre activity data for testing."""
    return {
        'is_compulsory': 1,
        'is_fixed': 0,
        'is_group': 1,
        'start_date': '2025-09-01',
        'end_date': '2025-12-31',
        'min_duration': 30,
        'max_duration': 60,
        'min_people_req': 4,
        'fixed_time_slots': '0-3,1-3,4-3',
    }


def test_init_success(mock_producer_manager):
    """Should initialize with exchange declaration"""
    publisher = CentreActivityPublisher(testing=True)

    assert publisher.exchange == 'activity.updates'
    assert publisher.testing is True
    assert publisher.manager is mock_producer_manager
    mock_producer_manager.declare_exchange.assert_called_once_with('activity.updates', 'topic') 

def test_init_exchange_declaration_failure(mock_producer_manager):
    """Should handle exchange declaration failure"""
    mock_producer_manager.declare_exchange.side_effect = Exception("Exchange error")

    publisher = CentreActivityPublisher(testing=True)

    assert publisher.exchange == 'activity.updates'
    assert publisher.manager is mock_producer_manager
    mock_producer_manager.declare_exchange.assert_called_once_with('activity.updates', 'topic')

# ==== publish_centre_activity_created tests ====
@patch('app.messaging.centre_activity_publisher.datetime')
@patch('app.messaging.centre_activity_publisher.uuid.uuid4')
def test_publish_centre_activity_created_success(mock_uuid, mock_datetime, mock_producer_manager, sample_centre_activity_data):
    """Should publish centre activity created message successfully"""
    # setup mocks
    mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
    fixed_datetime = datetime(2025, 1, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_datetime

    publisher = CentreActivityPublisher(testing=True)

    result = publisher.publish_centre_activity_created(
        centre_activity_id = 1,
        centre_activity_data = sample_centre_activity_data,
        created_by="user1"
    )

    assert result is True

    expected_message = {
        'correlation_id': '12345678-1234-5678-1234-567812345678',
        'event_type': 'CENTRE_ACTIVITY_CREATED',
        'centre_activity_id': 1,
        'centre_activity_data': sample_centre_activity_data,
        'created_by': 'user1',
        'timestamp': '2025-01-01T12:00:00'  # ISO format
    }
    mock_producer_manager.publish.assert_called_once_with(
        'activity.updates',
        'activity.centre_activity.created.1',
        expected_message
    )

def test_publish_centre_activity_created_failure(mock_producer_manager, sample_centre_activity_data):
    """Should return False when publish fails"""
    mock_producer_manager.publish.return_value = False

    publisher = CentreActivityPublisher(testing=True)

    result = publisher.publish_centre_activity_created(
        centre_activity_id = 1,
        centre_activity_data = sample_centre_activity_data,
        created_by="user1"
    )

    assert result is False
    mock_producer_manager.publish.assert_called_once()


# ==== publish_centre_activity_updated tests ====
@patch('app.messaging.centre_activity_publisher.datetime')
@patch('app.messaging.centre_activity_publisher.uuid.uuid4')
def test_publish_centre_activity_updated_success(mock_uuid, mock_datetime, mock_producer_manager, sample_centre_activity_data):
    """Should publich centre_activity updated message successfully"""
    # setup mocks
    mock_uuid.return_value = uuid.UUID('87654321-4321-8765-4321-876543218765')
    fixed_datetime = datetime(2025, 10, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_datetime

    publisher = CentreActivityPublisher(testing=True)

    old_data = sample_centre_activity_data
    new_data = {
        'is_compulsory': 0,
        'is_fixed': 1,
        'is_group': 0,
        'start_date': '2025-10-01',
        'end_date': '2025-12-01',
        'min_duration': 0,
        'max_duration': 30,
        'min_people_req': 0,
        'fixed_time_slots': '0-3,1-3,4-3',
    }
    changes = {
        'is_compulsory': {'old': old_data['is_compulsory'], 'new': new_data['is_compulsory']},
        'is_fixed': {'old': old_data['is_fixed'], 'new': new_data['is_fixed']},
        'is_group': {'old': old_data['is_group'], 'new': new_data['is_group']},
        'start_date': {'old': old_data['start_date'], 'new': new_data['start_date']},
        'end_date': {'old': old_data['end_date'], 'new': new_data['end_date']},
        'min_duration': {'old': old_data['min_duration'], 'new': new_data['min_duration']},
        'max_duration': {'old': old_data['max_duration'], 'new': new_data['max_duration']},
        'min_people_req': {'old': old_data['min_people_req'], 'new': new_data['min_people_req']},
        'fixed_time_slots': {'old': old_data['fixed_time_slots'], 'new': new_data['fixed_time_slots']},
    }

    result = publisher.publish_centre_activity_updated(
        centre_activity_id=1,
        old_data=old_data,
        new_data=new_data,
        changes=changes,
        modified_by="user2"
    )

    assert result is True

    expected_message = {
        'correlation_id': '87654321-4321-8765-4321-876543218765',
        'event_type': 'CENTRE_ACTIVITY_UPDATED',
        'centre_activity_id': 1,
        'old_data': old_data,
        'new_data': new_data,
        'changes': changes,
        'modified_by': 'user2',
        'timestamp': '2025-10-01T12:00:00'  # ISO format
    }

    mock_producer_manager.publish.assert_called_once_with(
        'activity.updates',
        'activity.centre_activity.updated.1',
        expected_message
    )

def test_publish_centre_activity_updated_failure(mock_producer_manager):
    """Should return False when publish fails"""
    mock_producer_manager.publish.return_value = False

    publisher = CentreActivityPublisher(testing=True)

    result = publisher.publish_centre_activity_updated(
        centre_activity_id=1,
        old_data={},
        new_data={},
        changes={},
        modified_by="user2"
    )

    assert result is False
    mock_producer_manager.publish.assert_called_once()

# ==== publish_centre_activity_deleted tests ====
@patch('app.messaging.centre_activity_publisher.datetime')
@patch('app.messaging.centre_activity_publisher.uuid.uuid4')
def test_publish_centre_activity_deleted_success(mock_uuid, mock_datetime, mock_producer_manager, sample_centre_activity_data):
    """Should publish centre_activity deleted message successfully"""
    # setup mocks
    mock_uuid.return_value = uuid.UUID('11223344-5566-7788-99aa-bbccddeeff00')
    fixed_datetime = datetime(2025, 5, 1, 12, 0, 0)
    mock_datetime.now.return_value = fixed_datetime

    publisher = CentreActivityPublisher(testing=True)

    result = publisher.publish_centre_activity_deleted(
        centre_activity_id=1,
        centre_activity_data=sample_centre_activity_data,
        deleted_by="user3"
    )

    assert result is True

    expected_message = {
        'correlation_id': '11223344-5566-7788-99aa-bbccddeeff00',
        'event_type': 'CENTRE_ACTIVITY_DELETED',
        'centre_activity_id': 1,
        'centre_activity_data': sample_centre_activity_data,
        'deleted_by': 'user3',
        'timestamp': '2025-05-01T12:00:00'  # ISO format
    }

    mock_producer_manager.publish.assert_called_once_with(
        'activity.updates',
        'activity.centre_activity.deleted.1',
        expected_message
    )

def test_publish_centre_activity_deleted_failure(mock_producer_manager, sample_centre_activity_data):
    """Should return False when publish fails"""
    mock_producer_manager.publish.return_value = False

    publisher = CentreActivityPublisher(testing=True)

    result = publisher.publish_centre_activity_deleted(
        centre_activity_id=1,
        centre_activity_data=sample_centre_activity_data,
        deleted_by="user3"
    )

    assert result is False
    mock_producer_manager.publish.assert_called_once()

# ==== close method test ====
def test_close(mock_producer_manager):
    """Close should be a no-op"""
    publisher = CentreActivityPublisher(testing=True)
    publisher.close()  # Should do nothing and not raise

# ==== Singleton instance tests ====
def test_get_activity_centre_activity_publisher_singleton(mock_producer_manager):
    """Should return singleton instance on multiple calls"""

    instance1 = get_centre_activity_publisher(testing=True)
    instance2 = get_centre_activity_publisher(testing=True)

    assert instance1 is instance2
    assert isinstance(instance1, CentreActivityPublisher)
    mock_producer_manager.declare_exchange.assert_called_once_with('activity.updates', 'topic')

#  ==== routing key format tests ====
def test_created_routing_key_format(mock_producer_manager, sample_centre_activity_data):
    """Should use correct routing key format for created event"""
    publisher = CentreActivityPublisher(testing=True)
    publisher.publish_centre_activity_created(
        centre_activity_id=42,
        centre_activity_data=sample_centre_activity_data,
        created_by="user1"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    assert args[1] == 'activity.centre_activity.created.42'

def test_updated_routing_key_format(mock_producer_manager, sample_centre_activity_data):
    """Should use correct routing key format for updated event"""
    publisher = CentreActivityPublisher(testing=True)
    publisher.publish_centre_activity_updated(
        centre_activity_id=43,
        old_data={},
        new_data={},
        changes={},
        modified_by="user2"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    assert args[1] == 'activity.centre_activity.updated.43'

def test_deleted_routing_key_format(mock_producer_manager, sample_centre_activity_data):
    """Should use correct routing key format for deleted event"""
    publisher = CentreActivityPublisher(testing=True)
    publisher.publish_centre_activity_deleted(
        centre_activity_id=44,
        centre_activity_data=sample_centre_activity_data,
        deleted_by="user3"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    assert args[1] == 'activity.centre_activity.deleted.44'

# === Message content structure tests === #
def test_created_message_structure(mock_producer_manager, sample_centre_activity_data):
    """Should construct correct message structure for created event"""
    publisher = CentreActivityPublisher(testing=True)
    publisher.publish_centre_activity_created(
        centre_activity_id=1,
        centre_activity_data=sample_centre_activity_data,
        created_by="user1"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    message = args[2]
    required_fields = [
        'correlation_id', 'event_type', 'centre_activity_id', 'centre_activity_data', 'created_by', 'timestamp'
    ]
    
    for field in required_fields:
        assert field in message
    assert message['event_type'] == 'CENTRE_ACTIVITY_CREATED'

def test_updated_message_structure(mock_producer_manager, sample_centre_activity_data):
    """Should construct correct message structure for updated event"""
    publisher = CentreActivityPublisher(testing=True)
    publisher.publish_centre_activity_updated(
        centre_activity_id=1,
        old_data={},
        new_data={},
        changes={},
        modified_by="user2"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    message = args[2]
    required_fields = [
        'correlation_id', 'event_type', 'centre_activity_id', 'old_data', 'new_data', 'changes',
        'modified_by', 'timestamp'
    ]
    
    for field in required_fields:
        assert field in message
    assert message['event_type'] == 'CENTRE_ACTIVITY_UPDATED'

def test_deleted_message_structure(mock_producer_manager, sample_centre_activity_data):
    """Should construct correct message structure for deleted event"""
    publisher = CentreActivityPublisher(testing=True)
    publisher.publish_centre_activity_deleted(
        centre_activity_id=1,
        centre_activity_data=sample_centre_activity_data,
        deleted_by="user3"
    )
    mock_producer_manager.publish.assert_called_once()
    args, kwargs = mock_producer_manager.publish.call_args
    message = args[2]
    required_fields = [
        'correlation_id', 'event_type', 'centre_activity_id', 'centre_activity_data', 'deleted_by', 'timestamp'
    ]
    
    for field in required_fields:
        assert field in message
    assert message['event_type'] == 'CENTRE_ACTIVITY_DELETED'
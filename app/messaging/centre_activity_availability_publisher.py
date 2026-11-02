import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from .producer_manager import get_producer_manager

logger = logging.getLogger(__name__)

class CentreActivityAvailabilityPublisher:
    """
    Publisher for Centre Activity Availability events.

    Normal CRUD goes through the outbox; this direct publisher is only used by the
    backfill sync script to push existing rows to the scheduler.
    """

    def __init__(self, testing: bool = False):
        self.manager = get_producer_manager(testing=testing)
        self.exchange = 'activity.updates'
        self.testing = testing

        # Declare the exchange
        try:
            self.manager.declare_exchange(self.exchange, 'topic')
            logger.info("Centre activity availability publisher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize centre activity availability publisher: {str(e)}")

    def publish_availability_created(self, availability_id: int, availability_data: Dict[str, Any],
                                     created_by: str, is_sync_event: bool = False,
                                     sync_reason: str = None) -> bool:
        """Publish availability creation event"""
        message = {
            'correlation_id': str(uuid.uuid4()).upper(),
            'event_type': 'CENTRE_ACTIVITY_AVAILABILITY_CREATED',
            'availability_id': availability_id,
            'availability_data': availability_data,
            'created_by': created_by,
            'timestamp': datetime.now().isoformat(),
            'is_sync_event': is_sync_event,
        }
        if sync_reason:
            message['sync_reason'] = sync_reason

        routing_key = f"activity.centre_activity_availability.created.{availability_id}"
        success = self.manager.publish(self.exchange, routing_key, message)

        if success:
            logger.info(f"Published CENTRE_ACTIVITY_AVAILABILITY_CREATED event for availability {availability_id}")
        else:
            logger.error(f"Failed to publish CENTRE_ACTIVITY_AVAILABILITY_CREATED event for availability {availability_id}")

        return success

    def close(self):
        """Close is handled by the producer manager"""
        pass


# Singleton instance
_availability_publisher = None

def get_centre_activity_availability_publisher(testing: bool = False) -> CentreActivityAvailabilityPublisher:
    """Get or create the singleton centre activity availability publisher instance"""
    global _availability_publisher
    if _availability_publisher is None:
        _availability_publisher = CentreActivityAvailabilityPublisher(testing=testing)
    return _availability_publisher

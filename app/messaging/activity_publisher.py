import logging
from typing import Dict, Any
from datetime import datetime

from .producer_manager import get_producer_manager

logger = logging.getLogger(__name__)

class ActivityPublisher:
    """Publisher for Activity Service: Activity events"""
    
    def __init__(self):
        self.manager = get_producer_manager()
        self.exchange = 'activity.updates'
        
        # Declare the exchange
        try:
            self.manager.declare_exchange(self.exchange, 'topic')
            logger.info("Activity publisher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize activity publisher: {str(e)}")
    
    def publish_activity_created(self, activity_id: int, activity_data: Dict[str, Any], 
                              created_by: str) -> bool:
        """Publish activity creation event"""
        message = {
            'event_type': 'ACTIVITY_CREATED',
            'activity_id': activity_id,
            'activity_data': activity_data,
            'created_by': created_by,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        routing_key = f"activity.created.{activity_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_CREATED event for activity {activity_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_CREATED event for activity {activity_id}")
            
        return success
    
    def publish_activity_updated(self, activity_id: int, old_data: Dict[str, Any], 
                              new_data: Dict[str, Any], changes: Dict[str, Any],
                              modified_by: str) -> bool:
        """Publish activity update event"""
        message = {
            'event_type': 'ACTIVITY_UPDATED',
            'activity_id': activity_id,
            'old_data': old_data,
            'new_data': new_data,
            'changes': changes,
            'modified_by': modified_by,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        routing_key = f"activity.updated.{activity_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_UPDATED event for activity {activity_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_UPDATED event for activity {activity_id}")
            
        return success
    
    def publish_activity_deleted(self, activity_id: int, activity_data: Dict[str, Any],
                              deleted_by: str) -> bool:
        """Publish activity deletion event"""
        message = {
            'event_type': 'ACTIVITY_DELETED',
            'activity_id': activity_id,
            'activity_data': activity_data,
            'deleted_by': deleted_by,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        routing_key = f"activity.deleted.{activity_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_DELETED event for activity {activity_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_DELETED event for activity {activity_id}")
            
        return success
    
    def close(self):
        """Close is handled by the producer manager"""
        # No need to close individual publishers
        # The producer manager handles the connection
        pass


# Singleton instance
_activity_publisher = None

def get_activity_publisher() -> ActivityPublisher:
    """Get or create the singleton activity publisher instance"""
    global _activity_publisher
    if _activity_publisher is None:
        _activity_publisher = ActivityPublisher()
    return _activity_publisher

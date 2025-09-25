import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from .producer_manager import get_producer_manager

logger = logging.getLogger(__name__)

class CentreActivityPublisher:
    """Publisher for Centre Activity Service events"""
    
    def __init__(self, testing: bool = False):
        self.manager = get_producer_manager(testing=testing)
        self.exchange = 'activity.updates'
        self.testing = testing
        
        # Declare the exchange
        try:
            self.manager.declare_exchange(self.exchange, 'topic')
            logger.info("Centre Activity publisher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize centre activity publisher: {str(e)}")
    
    def publish_centre_activity_created(self, centre_activity_id: int, centre_activity_data: Dict[str, Any], 
                                      created_by: str, correlation_id: str = None) -> bool:
        """Publish centre activity creation event"""
        message = {
            'correlation_id': correlation_id or str(uuid.uuid4()),
            'event_type': 'CENTRE_ACTIVITY_CREATED',
            'centre_activity_id': centre_activity_id,
            'centre_activity_data': centre_activity_data,
            'created_by': created_by,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        routing_key = f"activity.centre_activity.created.{centre_activity_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published CENTRE_ACTIVITY_CREATED event for centre activity {centre_activity_id}")
        else:
            logger.error(f"Failed to publish CENTRE_ACTIVITY_CREATED event for centre activity {centre_activity_id}")
            
        return success
    
    def publish_centre_activity_updated(self, centre_activity_id: int, old_data: Dict[str, Any], 
                                      new_data: Dict[str, Any], changes: Dict[str, Any],
                                      modified_by: str, correlation_id: str = None) -> bool:
        """Publish centre activity update event"""
        message = {
            'correlation_id': correlation_id or str(uuid.uuid4()),
            'event_type': 'CENTRE_ACTIVITY_UPDATED',
            'centre_activity_id': centre_activity_id,
            'old_data': old_data,
            'new_data': new_data,
            'changes': changes,
            'modified_by': modified_by,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        routing_key = f"activity.centre_activity.updated.{centre_activity_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published CENTRE_ACTIVITY_UPDATED event for centre activity {centre_activity_id}")
        else:
            logger.error(f"Failed to publish CENTRE_ACTIVITY_UPDATED event for centre activity {centre_activity_id}")
            
        return success
    
    def publish_centre_activity_deleted(self, centre_activity_id: int, centre_activity_data: Dict[str, Any],
                                      deleted_by: str, correlation_id: str = None) -> bool:
        """Publish centre activity deletion event"""
        message = {
            'correlation_id': correlation_id or str(uuid.uuid4()),
            'event_type': 'CENTRE_ACTIVITY_DELETED',
            'centre_activity_id': centre_activity_id,
            'centre_activity_data': centre_activity_data,
            'deleted_by': deleted_by,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        routing_key = f"activity.centre_activity.deleted.{centre_activity_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published CENTRE_ACTIVITY_DELETED event for centre activity {centre_activity_id}")
        else:
            logger.error(f"Failed to publish CENTRE_ACTIVITY_DELETED event for centre activity {centre_activity_id}")
            
        return success
    
    def close(self):
        """Close is handled by the producer manager"""
        # No need to close individual publishers
        # The producer manager handles the connection
        pass


# Singleton instance
_centre_activity_publisher = None

def get_centre_activity_publisher(testing: bool = False) -> CentreActivityPublisher:
    """Get or create the singleton centre activity publisher instance"""
    global _centre_activity_publisher
    if _centre_activity_publisher is None:
        _centre_activity_publisher = CentreActivityPublisher(testing=testing)
    return _centre_activity_publisher

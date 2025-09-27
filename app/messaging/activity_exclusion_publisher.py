import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from .producer_manager import get_producer_manager

logger = logging.getLogger(__name__)

class ActivityExclusionPublisher:
    """Publisher for Activity Exclusion Service events"""
    
    def __init__(self, testing: bool = False):
        self.manager = get_producer_manager(testing=testing)
        self.exchange = 'activity.updates'
        self.testing = testing
        
        # Declare the exchange
        try:
            self.manager.declare_exchange(self.exchange, 'topic')
            logger.info("Activity exclusion publisher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize activity exclusion publisher: {str(e)}")
    
    def publish_exclusion_created(self, exclusion_id: int, patient_id: int, 
                                centre_activity_id: int, exclusion_data: Dict[str, Any], 
                                created_by: str) -> bool:
        """Publish exclusion creation event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'ACTIVITY_EXCLUSION_CREATED',
            'exclusion_id': exclusion_id,
            'patient_id': patient_id,
            'centre_activity_id': centre_activity_id,
            'exclusion_data': exclusion_data,
            'created_by': created_by,
            'timestamp': datetime.now().isoformat()
        }
        
        routing_key = f"activity.centre_activity_exclusion.created.{exclusion_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_EXCLUSION_CREATED event for exclusion {exclusion_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_EXCLUSION_CREATED event for exclusion {exclusion_id}")
            
        return success
    
    def publish_exclusion_updated(self, exclusion_id: int, patient_id: int,
                                centre_activity_id: int, old_data: Dict[str, Any], 
                                new_data: Dict[str, Any], changes: Dict[str, Any],
                                modified_by: str) -> bool:
        """Publish exclusion update event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'ACTIVITY_EXCLUSION_UPDATED',
            'exclusion_id': exclusion_id,
            'patient_id': patient_id,
            'centre_activity_id': centre_activity_id,
            'old_data': old_data,
            'new_data': new_data,
            'changes': changes,
            'modified_by': modified_by,
            'timestamp': datetime.now().isoformat()
        }
        
        routing_key = f"activity.centre_activity_exclusion.updated.{exclusion_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_EXCLUSION_UPDATED event for exclusion {exclusion_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_EXCLUSION_UPDATED event for exclusion {exclusion_id}")
            
        return success
    
    def publish_exclusion_deleted(self, exclusion_id: int, patient_id: int,
                                centre_activity_id: int, exclusion_data: Dict[str, Any],
                                deleted_by: str) -> bool:
        """Publish exclusion deletion event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'ACTIVITY_EXCLUSION_DELETED',
            'exclusion_id': exclusion_id,
            'patient_id': patient_id,
            'centre_activity_id': centre_activity_id,
            'exclusion_data': exclusion_data,
            'deleted_by': deleted_by,
            'timestamp': datetime.now().isoformat()
        }
        
        routing_key = f"activity.centre_activity_exclusion.deleted.{exclusion_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_EXCLUSION_DELETED event for exclusion {exclusion_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_EXCLUSION_DELETED event for exclusion {exclusion_id}")
            
        return success
    
    def close(self):
        """Close is handled by the producer manager"""
        # No need to close individual publishers
        # The producer manager handles the connection
        pass


# Singleton instance
_exclusion_publisher = None

def get_activity_exclusion_publisher(testing: bool = False) -> ActivityExclusionPublisher:
    """Get or create the singleton activity exclusion publisher instance"""
    global _exclusion_publisher
    if _exclusion_publisher is None:
        _exclusion_publisher = ActivityExclusionPublisher(testing=testing)
    return _exclusion_publisher


# Usage examples and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Activity Exclusion Service Usage: python activity_exclusion_publisher.py test")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)

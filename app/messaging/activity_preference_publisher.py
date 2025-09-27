import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from .producer_manager import get_producer_manager

logger = logging.getLogger(__name__)

class ActivityPreferencePublisher:
    """Publisher for Activity Preference Service events"""
    
    def __init__(self, testing: bool = False):
        self.manager = get_producer_manager(testing=testing)
        self.exchange = 'activity.updates'
        self.testing = testing
        
        # Declare the exchange
        try:
            self.manager.declare_exchange(self.exchange, 'topic')
            logger.info("Activity preference publisher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize activity preference publisher: {str(e)}")
    
    def publish_preference_created(self, preference_id: int, patient_id: int, 
                                 centre_activity_id: int, preference_data: Dict[str, Any], 
                                 created_by: str) -> bool:
        """Publish preference creation event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'ACTIVITY_PREFERENCE_CREATED',
            'preference_id': preference_id,
            'patient_id': patient_id,
            'centre_activity_id': centre_activity_id,
            'preference_data': preference_data,
            'created_by': created_by,
            'timestamp': datetime.now().isoformat()
        }
        
        routing_key = f"activity.preference.created.{centre_activity_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_PREFERENCE_CREATED event for preference {preference_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_PREFERENCE_CREATED event for preference {preference_id}")
            
        return success
    
    def publish_preference_updated(self, preference_id: int, patient_id: int,
                                 centre_activity_id: int, old_data: Dict[str, Any], 
                                 new_data: Dict[str, Any], changes: Dict[str, Any],
                                 modified_by: str) -> bool:
        """Publish preference update event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'ACTIVITY_PREFERENCE_UPDATED',
            'preference_id': preference_id,
            'patient_id': patient_id,
            'centre_activity_id': centre_activity_id,
            'old_data': old_data,
            'new_data': new_data,
            'changes': changes,
            'modified_by': modified_by,
            'timestamp': datetime.now().isoformat()
        }
        
        routing_key = f"activity.preference.updated.{centre_activity_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_PREFERENCE_UPDATED event for preference {preference_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_PREFERENCE_UPDATED event for preference {preference_id}")
            
        return success
    
    def publish_preference_deleted(self, preference_id: int, patient_id: int,
                                 centre_activity_id: int, preference_data: Dict[str, Any],
                                 deleted_by: str) -> bool:
        """Publish preference deletion event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'ACTIVITY_PREFERENCE_DELETED',
            'preference_id': preference_id,
            'patient_id': patient_id,
            'centre_activity_id': centre_activity_id,
            'preference_data': preference_data,
            'deleted_by': deleted_by,
            'timestamp': datetime.now().isoformat()
        }
        
        routing_key = f"activity.preference.deleted.{centre_activity_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_PREFERENCE_DELETED event for preference {preference_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_PREFERENCE_DELETED event for preference {preference_id}")
            
        return success
    
    def close(self):
        """Close is handled by the producer manager"""
        # No need to close individual publishers
        # The producer manager handles the connection
        pass


# Singleton instance
_preference_publisher = None

def get_activity_preference_publisher(testing: bool = False) -> ActivityPreferencePublisher:
    """Get or create the singleton activity preference publisher instance"""
    global _preference_publisher
    if _preference_publisher is None:
        _preference_publisher = ActivityPreferencePublisher(testing=testing)
    return _preference_publisher


# Usage examples and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Activity Preference Service Usage: python activity_preference_publisher.py test")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)


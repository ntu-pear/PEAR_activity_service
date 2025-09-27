import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from .producer_manager import get_producer_manager

logger = logging.getLogger(__name__)

class ActivityRecommendationPublisher:
    """Publisher for Activity Recommendation Service events"""
    
    def __init__(self, testing: bool = False):
        self.manager = get_producer_manager(testing=testing)
        self.exchange = 'activity.updates'
        self.testing = testing
        
        # Declare the exchange
        try:
            self.manager.declare_exchange(self.exchange, 'topic')
            logger.info("Activity recommendation publisher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize activity recommendation publisher: {str(e)}")
    
    def publish_recommendation_created(self, recommendation_id: int, patient_id: int, 
                                     centre_activity_id: int, doctor_id: str,
                                     recommendation_data: Dict[str, Any], 
                                     created_by: str) -> bool:
        """Publish activity recommendation creation event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'ACTIVITY_RECOMMENDATION_CREATED',
            'recommendation_id': recommendation_id,
            'patient_id': patient_id,
            'centre_activity_id': centre_activity_id,
            'doctor_id': doctor_id,
            'recommendation_data': recommendation_data,
            'created_by': created_by,
            'timestamp': datetime.now().isoformat()
        }
        
        routing_key = f"activity.recommendation.created.{recommendation_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_RECOMMENDATION_CREATED event for recommendation {recommendation_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_RECOMMENDATION_CREATED event for recommendation {recommendation_id}")
            
        return success
    
    def publish_recommendation_updated(self, recommendation_id: int, patient_id: int,
                                     centre_activity_id: int, doctor_id: str,
                                     old_data: Dict[str, Any], new_data: Dict[str, Any], 
                                     changes: Dict[str, Any], modified_by: str) -> bool:
        """Publish recommendation update event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'ACTIVITY_RECOMMENDATION_UPDATED',
            'recommendation_id': recommendation_id,
            'patient_id': patient_id,
            'centre_activity_id': centre_activity_id,
            'doctor_id': doctor_id,
            'old_data': old_data,
            'new_data': new_data,
            'changes': changes,
            'modified_by': modified_by,
            'timestamp': datetime.now().isoformat()
        }
        
        routing_key = f"activity.recommendation.updated.{recommendation_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_RECOMMENDATION_UPDATED event for recommendation {recommendation_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_RECOMMENDATION_UPDATED event for recommendation {recommendation_id}")
            
        return success
    
    def publish_recommendation_deleted(self, recommendation_id: int, patient_id: int,
                                     centre_activity_id: int, doctor_id: str,
                                     recommendation_data: Dict[str, Any],
                                     deleted_by: str) -> bool:
        """Publish recommendation deletion event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'ACTIVITY_RECOMMENDATION_DELETED',
            'recommendation_id': recommendation_id,
            'patient_id': patient_id,
            'centre_activity_id': centre_activity_id,
            'doctor_id': doctor_id,
            'recommendation_data': recommendation_data,
            'deleted_by': deleted_by,
            'timestamp': datetime.now().isoformat()
        }
        
        routing_key = f"activity.recommendation.deleted.{recommendation_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published ACTIVITY_RECOMMENDATION_DELETED event for recommendation {recommendation_id}")
        else:
            logger.error(f"Failed to publish ACTIVITY_RECOMMENDATION_DELETED event for recommendation {recommendation_id}")
            
        return success
    
    def close(self):
        """Close is handled by the producer manager"""
        # No need to close individual publishers
        # The producer manager handles the connection
        pass


# Singleton instance
_recommendation_publisher = None

def get_activity_recommendation_publisher(testing: bool = False) -> ActivityRecommendationPublisher:
    """Get or create the singleton activity recommendation publisher instance"""
    global _recommendation_publisher
    if _recommendation_publisher is None:
        _recommendation_publisher = ActivityRecommendationPublisher(testing=testing)
    return _recommendation_publisher


# Usage examples and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Activity Recommendation Service Usage: python activity_recommendation_publisher.py test")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)

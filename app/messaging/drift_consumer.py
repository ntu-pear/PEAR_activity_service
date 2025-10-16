import logging
import threading
import json
import uuid
from typing import Dict, Any, Optional
from contextlib import contextmanager

from .rabbitmq_client import RabbitMQClient
from .producer_manager import get_producer_manager

logger = logging.getLogger(__name__)


class DriftConsumer:
    """
    Consumer for drift detection notifications from reconciliation service.
    
    Handles drift by republishing UPDATE sync events for all entity types.
    Since we use soft deletes, there's no need for separate DELETE handlers.
    """
    
    def __init__(self):
        self.client = RabbitMQClient("activity-drift-consumer")
        self.drift_queue = "reconciliation.drift.detected"
        self.shutdown_event = None
        self.is_consuming = False
        
        # Import dependencies
        from app.database import SessionLocal
        
        self.SessionLocal = SessionLocal
        self.producer_manager = get_producer_manager()
        self.exchange = 'activity.updates'
        
        # Import models
        from app.models.activity_model import Activity
        from app.models.centre_activity_model import CentreActivity
        from app.models.centre_activity_preference_model import CentreActivityPreference
        from app.models.centre_activity_recommendation_model import CentreActivityRecommendation
        from app.models.centre_activity_exclusion_model import CentreActivityExclusion
        
        self.Activity = Activity
        self.CentreActivity = CentreActivity
        self.CentreActivityPreference = CentreActivityPreference
        self.CentreActivityRecommendation = CentreActivityRecommendation
        self.CentreActivityExclusion = CentreActivityExclusion
    
    @contextmanager
    def get_db_session(self):
        """Context manager for database sessions with proper cleanup"""
        db = self.SessionLocal()
        try:
            yield db
        except Exception as e:
            logger.error(f"Rolling back session due to error: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def _flush_logs(self):
        """Force flush all log handlers"""
        try:
            for handler in logging.getLogger().handlers:
                handler.flush()
            for handler in logger.handlers:
                handler.flush()
        except Exception:
            pass
    
    def set_shutdown_event(self, shutdown_event: threading.Event):
        """Set the shutdown event for graceful shutdown"""
        self.shutdown_event = shutdown_event
        if self.client:
            self.client.set_shutdown_event(shutdown_event)
    
    def setup_consumer(self):
        """Set up consumer to listen to drift detection queue"""
        try:
            self.client.connect()
            
            self.client.channel.exchange_declare(
                exchange='reconciliation.events',
                exchange_type='topic',
                durable=True
            )
            
            self.client.consume(self.drift_queue, self._handle_message_wrapper)
            logger.info(f"Drift consumer set up for queue: {self.drift_queue}")
            
        except Exception as e:
            logger.error(f"Failed to setup drift consumer: {str(e)}")
            raise
    
    def start_consuming(self):
        """Start consuming messages"""
        try:
            self.setup_consumer()
            logger.info("Starting drift consumer...")
            self.is_consuming = True
            self.client.start_consuming()
        except Exception as e:
            logger.error(f"Error starting drift consumer: {str(e)}")
            raise
        finally:
            self.is_consuming = False
    
    def stop(self):
        """Stop the consumer gracefully"""
        logger.info("Stopping drift consumer...")
        self.is_consuming = False
        if self.client:
            self.client.stop_consuming()
    
    def _handle_message_wrapper(self, message: Dict[str, Any]) -> bool:
        """Wrapper for message handling with proper acknowledgment logic"""
        try:
            record_type = message.get('data', {}).get('record_type', 'UNKNOWN')
            record_id = message.get('data', {}).get('record_id', 'UNKNOWN')
            logger.debug(f"RECEIVED DRIFT: type={record_type}, id={record_id}")
            
            if self.shutdown_event and self.shutdown_event.is_set():
                logger.info("Shutdown signal received")
                return False
            
            success = self._process_drift_message(message)
            self._flush_logs()
            
            return success
                
        except Exception as e:
            logger.error(f"Fatal error in message wrapper: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._flush_logs()
            return False
    
    def _process_drift_message(self, message: Dict[str, Any]) -> bool:
        """Process drift detection message"""
        try:
            message_data = self._parse_message(message)
            if not message_data:
                return False
            
            record_type = message_data['record_type']
            record_id = message_data['record_id']
            drift_type = message_data.get('drift_type', 'unknown')
            
            logger.info(f"Processing drift: {record_type} id={record_id} type={drift_type}")
            
            # Map record types to handlers
            handlers = {
                "activity": (self.Activity, self._publish_activity_sync),
                "centre_activity": (self.CentreActivity, self._publish_centre_activity_sync),
                "centre_activity_preference": (self.CentreActivityPreference, self._publish_preference_sync),
                "centre_activity_recommendation": (self.CentreActivityRecommendation, self._publish_recommendation_sync),
                "centre_activity_exclusion": (self.CentreActivityExclusion, self._publish_exclusion_sync),
            }
            
            handler_info = handlers.get(record_type)
            if not handler_info:
                logger.warning(f"Unknown record_type: {record_type}")
                return False
            
            model_class, publish_func = handler_info
            
            # Fetch the record (including soft-deleted ones for sync)
            with self.get_db_session() as db:
                record = db.query(model_class).filter(
                    model_class.id == record_id
                ).first()
                
                if not record:
                    logger.warning(f"{record_type} {record_id} not found in source - skipping sync")
                    return True  # Acknowledge - nothing to sync
                
                # Publish sync event with complete data
                return publish_func(record)
            
        except Exception as e:
            logger.error(f"Error processing drift message: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _parse_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse and validate message structure"""
        try:
            message_data = message.get('data', {})
            
            required_fields = ['record_type', 'record_id']
            for field in required_fields:
                if field not in message_data:
                    logger.error(f"Missing required field '{field}'")
                    return None
            
            return message_data
            
        except Exception as e:
            logger.error(f"Failed to parse message: {str(e)}")
            return None
    
    # ========================
    # RECONCILER WILL TRIGGER THESE SYNC PUBLISHERS
    # All use UPDATE event type with "new_data" field
    # ========================
    
    def _publish_activity_sync(self, activity) -> bool:
        """Publish activity sync event (UPDATE)"""
        try:
            correlation_id = str(uuid.uuid4())
            
            # Complete entity data in new_data
            entity_data = {
                "id": activity.id,
                "title": activity.title,
                "description": activity.description,
                "is_deleted": activity.is_deleted,
                "created_date": activity.created_date.isoformat() if activity.created_date else None,
                "modified_date": activity.modified_date.isoformat() if activity.modified_date else None,
                "created_by_id": activity.created_by_id,
                "modified_by_id": activity.modified_by_id
            }
            
            message = {
                "correlation_id": correlation_id,
                "event_type": "ACTIVITY_UPDATED",
                "activity_id": activity.id,
                "old_data": {},
                "new_data": entity_data,
                "changes": {},
                "modified_by": activity.modified_by_id or "drift_reconciliation",
                "modified_by_name": "Drift Reconciliation",
                "timestamp": activity.modified_date.isoformat() if activity.modified_date else None,
                "is_sync_event": True,
                "sync_reason": "drift_detected"
            }
            
            success = self.producer_manager.publish(
                self.exchange, 
                "activity.updated.sync", 
                message
            )
            
            if success:
                logger.info(f"Published activity sync for id={activity.id}")
            return success
            
        except Exception as e:
            logger.error(f"Error publishing activity sync: {str(e)}")
            return False

    def _publish_centre_activity_sync(self, centre_activity) -> bool:
        """Publish centre activity sync event (UPDATE)"""
        try:
            correlation_id = str(uuid.uuid4())
            
            entity_data = {
                "id": centre_activity.id,
                "activity_id": centre_activity.activity_id,
                "is_deleted": centre_activity.is_deleted,
                "is_compulsory": centre_activity.is_compulsory,
                "is_fixed": centre_activity.is_fixed,
                "is_group": centre_activity.is_group,
                "start_date": centre_activity.start_date.isoformat() if centre_activity.start_date else None,
                "end_date": centre_activity.end_date.isoformat() if centre_activity.end_date else None,
                "min_duration": centre_activity.min_duration,
                "max_duration": centre_activity.max_duration,
                "min_people_req": centre_activity.min_people_req,
                "fixed_time_slots": centre_activity.fixed_time_slots,
                "created_date": centre_activity.created_date.isoformat() if centre_activity.created_date else None,
                "modified_date": centre_activity.modified_date.isoformat() if centre_activity.modified_date else None,
                "created_by_id": centre_activity.created_by_id,
                "modified_by_id": centre_activity.modified_by_id
            }
            
            message = {
                "correlation_id": correlation_id,
                "event_type": "CENTRE_ACTIVITY_UPDATED",
                "centre_activity_id": centre_activity.id,
                "old_data": {},
                "new_data": entity_data,
                "changes": {},
                "modified_by": centre_activity.modified_by_id or "drift_reconciliation",
                "modified_by_name": "Drift Reconciliation",
                "timestamp": centre_activity.modified_date.isoformat() if centre_activity.modified_date else None,
                "is_sync_event": True,
                "sync_reason": "drift_detected"
            }
            
            success = self.producer_manager.publish(
                self.exchange,
                "activity.centre_activity.updated.sync",
                message
            )
            
            if success:
                logger.info(f"Published centre_activity sync for id={centre_activity.id}")
            return success
            
        except Exception as e:
            logger.error(f"Error publishing centre_activity sync: {str(e)}")
            return False

    def _publish_preference_sync(self, preference) -> bool:
        """Publish preference sync event (UPDATE)"""
        try:
            correlation_id = str(uuid.uuid4())
            
            entity_data = {
                "id": preference.id,
                "centre_activity_id": preference.centre_activity_id,
                "patient_id": preference.patient_id,
                "is_like": preference.is_like,
                "is_deleted": preference.is_deleted,
                "created_date": preference.created_date.isoformat() if preference.created_date else None,
                "modified_date": preference.modified_date.isoformat() if preference.modified_date else None,
                "created_by_id": preference.created_by_id,
                "modified_by_id": preference.modified_by_id
            }
            
            message = {
                "correlation_id": correlation_id,
                "event_type": "ACTIVITY_PREFERENCE_UPDATED",
                "preference_id": preference.id,
                "old_data": {},
                "new_data": entity_data,
                "changes": {},
                "modified_by": preference.modified_by_id or "drift_reconciliation",
                "modified_by_name": "Drift Reconciliation",
                "timestamp": preference.modified_date.isoformat() if preference.modified_date else None,
                "is_sync_event": True,
                "sync_reason": "drift_detected"
            }
            
            success = self.producer_manager.publish(
                self.exchange,
                "activity.preference.updated.sync",
                message
            )
            
            if success:
                logger.info(f"Published preference sync for id={preference.id}")
            return success
            
        except Exception as e:
            logger.error(f"Error publishing preference sync: {str(e)}")
            return False

    def _publish_recommendation_sync(self, recommendation) -> bool:
        """Publish recommendation sync event (UPDATE)"""
        try:
            correlation_id = str(uuid.uuid4())
            
            entity_data = {
                "id": recommendation.id,
                "centre_activity_id": recommendation.centre_activity_id,
                "patient_id": recommendation.patient_id,
                "doctor_id": recommendation.doctor_id,
                "doctor_recommendation": recommendation.doctor_recommendation,
                "doctor_remarks": recommendation.doctor_remarks,
                "is_deleted": recommendation.is_deleted,
                "created_date": recommendation.created_date.isoformat() if recommendation.created_date else None,
                "modified_date": recommendation.modified_date.isoformat() if recommendation.modified_date else None,
                "created_by_id": recommendation.created_by_id,
                "modified_by_id": recommendation.modified_by_id
            }
            
            message = {
                "correlation_id": correlation_id,
                "event_type": "ACTIVITY_RECOMMENDATION_UPDATED",
                "recommendation_id": recommendation.id,
                "old_data": {},
                "new_data": entity_data,
                "changes": {},
                "modified_by": recommendation.modified_by_id or "drift_reconciliation",
                "modified_by_name": "Drift Reconciliation",
                "timestamp": recommendation.modified_date.isoformat() if recommendation.modified_date else None,
                "is_sync_event": True,
                "sync_reason": "drift_detected"
            }
            
            success = self.producer_manager.publish(
                self.exchange,
                "activity.recommendation.updated.sync",
                message
            )
            
            if success:
                logger.info(f"Published recommendation sync for id={recommendation.id}")
            return success
            
        except Exception as e:
            logger.error(f"Error publishing recommendation sync: {str(e)}")
            return False

    def _publish_exclusion_sync(self, exclusion) -> bool:
        """Publish exclusion sync event (UPDATE)"""
        try:
            correlation_id = str(uuid.uuid4())
            
            entity_data = {
                "id": exclusion.id,
                "centre_activity_id": exclusion.centre_activity_id,
                "patient_id": exclusion.patient_id,
                "is_deleted": exclusion.is_deleted,
                "exclusion_remarks": exclusion.exclusion_remarks,
                "start_date": exclusion.start_date.isoformat() if exclusion.start_date else None,
                "end_date": exclusion.end_date.isoformat() if exclusion.end_date else None,
                "created_date": exclusion.created_date.isoformat() if exclusion.created_date else None,
                "modified_date": exclusion.modified_date.isoformat() if exclusion.modified_date else None,
                "created_by_id": exclusion.created_by_id,
                "modified_by_id": exclusion.modified_by_id
            }
            
            message = {
                "correlation_id": correlation_id,
                "event_type": "ACTIVITY_EXCLUSION_UPDATED",
                "exclusion_id": exclusion.id,
                "old_data": {},
                "new_data": entity_data,
                "changes": {},
                "modified_by": exclusion.modified_by_id or "drift_reconciliation",
                "modified_by_name": "Drift Reconciliation",
                "timestamp": exclusion.modified_date.isoformat() if exclusion.modified_date else None,
                "is_sync_event": True,
                "sync_reason": "drift_detected"
            }
            
            success = self.producer_manager.publish(
                self.exchange,
                "activity.centre_activity_exclusion.updated.sync",
                message
            )
            
            if success:
                logger.info(f"Published exclusion sync for id={exclusion.id}")
            return success
            
        except Exception as e:
            logger.error(f"Error publishing exclusion sync: {str(e)}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for monitoring"""
        try:
            return {
                "status": "healthy",
                "service": "drift_consumer",
                "is_consuming": self.is_consuming,
                "queue": self.drift_queue,
                "rabbitmq_connected": self.client.is_connected if self.client else False
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def close(self):
        """Close connections"""
        if self.client:
            self.client.close()
            logger.info("Drift consumer connections closed")

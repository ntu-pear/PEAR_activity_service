import sys
import os
import argparse
from typing import List, Optional, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from .base_script import BaseScript

class ActivitySyncScript(BaseScript):
    """
    Script to emit ACTIVITY_UPDATED events for existing activities in the database
    """
    
    def __init__(self, dry_run: bool = False, batch_size: int = 100):
        super().__init__(dry_run, batch_size)
        
        # Initialize database and messaging
        self._init_dependencies()
    
    def _init_dependencies(self):
        """Initialize database and messaging dependencies"""
        try:
            # Setup proper Python paths
            script_dir = os.path.dirname(os.path.abspath(__file__))
            current = script_dir
            project_root = None
            
            # Find project root (directory containing 'app')
            for _ in range(5):
                if 'app' in os.listdir(current) and os.path.isdir(os.path.join(current, 'app')):
                    project_root = current
                    break
                parent = os.path.dirname(current)
                if parent == current:
                    break
                current = parent
            
            if not project_root:
                raise RuntimeError("Could not find project root directory containing 'app'")
            
            app_dir = os.path.join(project_root, 'app')
            
            # Add to Python path
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            if app_dir not in sys.path:
                sys.path.insert(0, app_dir)
            
            self.logger.info(f"Project root: {project_root}")
            self.logger.info(f"App directory: {app_dir}")
            
            # Import database dependencies
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import create_engine, func
            from database import get_database_url
            from app.models.activity_model import Activity
            
            # Import messaging dependencies  
            from messaging.activity_publisher import get_activity_publisher
            
            # Set up database
            engine = create_engine(get_database_url())
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.Activity = Activity
            self.func = func
            
            # Set up messaging
            self.publisher = get_activity_publisher()
            
            self.logger.info("Dependencies initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dependencies: {str(e)}")
            raise
    
    def get_total_count(self) -> int:
        """Get total number of activities in the database"""
        try:
            with self.SessionLocal() as db:
                # Count activities
                count = db.query(self.func.count(self.Activity.id)).scalar()
                
                self.logger.info(f"Found {count} activities in database")
                return count
                
        except Exception as e:
            self.logger.error(f"Error getting activity count: {str(e)}")
            raise
    
    def fetch_batch(self, offset: int, limit: int) -> List[Any]:
        """Fetch a batch of activities from the database"""
        try:
            with self.SessionLocal() as db:
                activities = db.query(self.Activity).order_by(self.Activity.id).offset(offset).limit(limit).all()
                
                self.logger.debug(f"Fetched {len(activities)} activities from offset {offset}")
                return activities
                
        except Exception as e:
            self.logger.error(f"Error fetching activity batch: {str(e)}")
            raise
    
    def process_item(self, activity) -> bool:
        """Process a single activity - emit ACTIVITY_UPDATED event"""
        try:
            activity_id = activity.id
            
            # Convert activity model to dictionary
            activity_data = self._activity_to_dict(activity)
            
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would emit ACTIVITY_UPDATED for activity {activity_id} ({activity.title})")
                self.logger.debug(f"Activity data: {activity_data}")
                return True
            
            # Emit ACTIVITY_UPDATED event
            success = self.publisher.publish_activity_created(
                activity_id,
                activity_data,
                "sync_script")
            
            if success:
                self.logger.info(f"Emitted ACTIVITY_UPDATED event for activity {activity_id} ({activity.title})")
                return True
            else:
                self.logger.error(f"Failed to emit ACTIVITY_UPDATED event for activity {activity_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing activity {getattr(activity, 'id', 'unknown')}: {str(e)}")
            raise
    
    def _activity_to_dict(self, activity) -> Dict[str, Any]:
        """Convert activity model to dictionary for messaging"""
        try:
            activity_dict = {}
            
            # Get all activity attributes
            for column in activity.__table__.columns:
                value = getattr(activity, column.name)
                
                # Convert datetime objects to ISO format strings
                if hasattr(value, 'isoformat'):
                    activity_dict[column.name] = value.isoformat()
                else:
                    activity_dict[column.name] = value
            
            return activity_dict
            
        except Exception as e:
            self.logger.error(f"Error converting activity to dict: {str(e)}")
            return {}


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Emit ACTIVITY_UPDATED events for existing activities')
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual events emitted)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of activities to process per batch (default: 100)')
    
    args = parser.parse_args()
    
    try:
        # Create and run the script
        script = ActivitySyncScript(
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
        
        script.run()
            
    except KeyboardInterrupt:
        print("Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Script failed: {str(e)}")
        sys.exit(1)
    finally:
        # Ensure all messages are published before exiting
        print("Shutting down producer manager...")
        from messaging.producer_manager import stop_producer_manager
        stop_producer_manager()
        print("Producer manager stopped. Script complete.")

if __name__ == "__main__":
    main()

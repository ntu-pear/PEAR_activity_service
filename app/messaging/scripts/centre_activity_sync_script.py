import sys
import os
import argparse
from typing import List, Optional, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from .base_script import BaseScript

class CentreActivitySyncScript(BaseScript):
    """
    Script to emit CENTRE_ACTIVITY_CREATED events for existing centre activities in the database
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
            
            # Import all models to ensure relationships are properly initialized
            # SQLAlchemy needs all referenced models to be imported before creating sessions
            try:
                from app.models.activity_model import Activity
                from app.models.centre_activity_model import CentreActivity
                self.logger.debug("Models imported successfully")
            except ImportError as e:
                self.logger.error(f"Failed to import models: {e}")
                raise
            
            # Import messaging dependencies  
            from messaging.centre_activity_publisher import get_centre_activity_publisher
            
            # Set up database
            engine = create_engine(get_database_url())
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.Activity = Activity
            self.CentreActivity = CentreActivity
            self.func = func
            
            # Set up messaging
            self.publisher = get_centre_activity_publisher()
            
            self.logger.info("Dependencies initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dependencies: {str(e)}")
            raise
    
    def get_total_count(self) -> int:
        """Get total number of centre activities in the database"""
        try:
            with self.SessionLocal() as db:
                # Count centre activities
                count = db.query(self.func.count(self.CentreActivity.id)).scalar()
                
                self.logger.info(f"Found {count} centre activities in database")
                return count
                
        except Exception as e:
            self.logger.error(f"Error getting centre activity count: {str(e)}")
            raise
    
    def fetch_batch(self, offset: int, limit: int) -> List[Any]:
        """Fetch a batch of centre activities from the database"""
        try:
            with self.SessionLocal() as db:
                centre_activities = db.query(self.CentreActivity).order_by(self.CentreActivity.id).offset(offset).limit(limit).all()
                
                self.logger.debug(f"Fetched {len(centre_activities)} centre activities from offset {offset}")
                return centre_activities
                
        except Exception as e:
            self.logger.error(f"Error fetching centre activity batch: {str(e)}")
            raise
    
    def process_item(self, centre_activity) -> bool:
        """Process a single centre activity - emit CENTRE_ACTIVITY_CREATED event"""
        try:
            centre_activity_id = centre_activity.id
            
            # Convert centre activity model to dictionary
            centre_activity_data = self._centre_activity_to_dict(centre_activity)
            
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would emit CENTRE_ACTIVITY_CREATED for centre activity {centre_activity_id} (Activity: {centre_activity.activity_id})")
                self.logger.debug(f"Centre activity data: {centre_activity_data}")
                return True
            
            # Emit CENTRE_ACTIVITY_CREATED event
            success = self.publisher.publish_centre_activity_created(
                centre_activity_id,
                centre_activity_data,
                "sync_script"
            )
            
            if success:
                self.logger.info(f"Emitted CENTRE_ACTIVITY_CREATED event for centre activity {centre_activity_id} (Activity: {centre_activity.activity_id})")
                return True
            else:
                self.logger.error(f"Failed to emit CENTRE_ACTIVITY_CREATED event for centre activity {centre_activity_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing centre activity {getattr(centre_activity, 'id', 'unknown')}: {str(e)}")
            raise
    
    def _centre_activity_to_dict(self, centre_activity) -> Dict[str, Any]:
        """Convert centre activity model to dictionary for messaging"""
        try:
            centre_activity_dict = {}
            
            # Manually extract attributes to avoid relationship issues
            centre_activity_dict['id'] = centre_activity.id
            centre_activity_dict['activity_id'] = centre_activity.activity_id
            centre_activity_dict['is_deleted'] = centre_activity.is_deleted
            centre_activity_dict['is_compulsory'] = centre_activity.is_compulsory
            centre_activity_dict['is_fixed'] = centre_activity.is_fixed
            centre_activity_dict['is_group'] = centre_activity.is_group
            centre_activity_dict['min_duration'] = centre_activity.min_duration
            centre_activity_dict['max_duration'] = centre_activity.max_duration
            centre_activity_dict['min_people_req'] = centre_activity.min_people_req
            centre_activity_dict['fixed_time_slots'] = centre_activity.fixed_time_slots
            centre_activity_dict['created_by_id'] = centre_activity.created_by_id
            centre_activity_dict['modified_by_id'] = centre_activity.modified_by_id
            
            # Handle datetime fields
            if hasattr(centre_activity.start_date, 'isoformat'):
                centre_activity_dict['start_date'] = centre_activity.start_date.isoformat()
            else:
                centre_activity_dict['start_date'] = str(centre_activity.start_date)
                
            if hasattr(centre_activity.end_date, 'isoformat'):
                centre_activity_dict['end_date'] = centre_activity.end_date.isoformat()
            else:
                centre_activity_dict['end_date'] = str(centre_activity.end_date)
                
            if centre_activity.created_date and hasattr(centre_activity.created_date, 'isoformat'):
                centre_activity_dict['created_date'] = centre_activity.created_date.isoformat()
            elif centre_activity.created_date:
                centre_activity_dict['created_date'] = str(centre_activity.created_date)
            else:
                centre_activity_dict['created_date'] = None
                
            if centre_activity.modified_date and hasattr(centre_activity.modified_date, 'isoformat'):
                centre_activity_dict['modified_date'] = centre_activity.modified_date.isoformat()
            elif centre_activity.modified_date:
                centre_activity_dict['modified_date'] = str(centre_activity.modified_date)
            else:
                centre_activity_dict['modified_date'] = None
            
            return centre_activity_dict
            
        except Exception as e:
            self.logger.error(f"Error converting centre activity to dict: {str(e)}")
            return {}


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Emit CENTRE_ACTIVITY_CREATED events for existing centre activities')
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual events emitted)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of centre activities to process per batch (default: 100)')
    
    args = parser.parse_args()
    
    try:
        # Create and run the script
        script = CentreActivitySyncScript(
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


if __name__ == "__main__":
    main()

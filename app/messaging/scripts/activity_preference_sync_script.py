import sys
import os
import argparse
from typing import List, Optional, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from .base_script import BaseScript

class ActivityPreferenceSyncScript(BaseScript):
    """
    Script to emit PREFERENCE_UPDATED events for existing activity preferences in the database
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
            from app.models.centre_activity_preference_model import CentreActivityPreference
            
            # Import messaging dependencies  
            from messaging.activity_preference_publisher import get_activity_preference_publisher
            
            # Set up database
            engine = create_engine(get_database_url())
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.CentreActivityPreference = CentreActivityPreference
            self.func = func
            
            # Set up messaging
            self.publisher = get_activity_preference_publisher()
            
            self.logger.info("Dependencies initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dependencies: {str(e)}")
            raise
    
    def get_total_count(self) -> int:
        """Get total number of activity preferences in the database"""
        try:
            with self.SessionLocal() as db:
                # Count preferences
                count = db.query(self.func.count(self.CentreActivityPreference.id)).scalar()
                
                self.logger.info(f"Found {count} preferences in database")
                return count
                
        except Exception as e:
            self.logger.error(f"Error getting preference count: {str(e)}")
            raise
    
    def fetch_batch(self, offset: int, limit: int) -> List[Any]:
        """Fetch a batch of preferences from the database"""
        try:
            with self.SessionLocal() as db:
                preferences = db.query(self.CentreActivityPreference).order_by(self.CentreActivityPreference.id).offset(offset).limit(limit).all()
                
                self.logger.debug(f"Fetched {len(preferences)} preferences from offset {offset}")
                return preferences
                
        except Exception as e:
            self.logger.error(f"Error fetching preference batch: {str(e)}")
            raise
    
    def process_item(self, preference) -> bool:
        """Process a single preference - emit ACTIVITY_PREFERENCE_CREATED event"""
        try:
            preference_id = preference.id
            
            # Convert preference model to dictionary
            preference_data = self._preference_to_dict(preference)
            
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would emit ACTIVITY_PREFERENCE_CREATED for preference {preference_id} (Patient: {preference.patient_id})")
                self.logger.debug(f"Preference data: {preference_data}")
                return True
            
            # Emit ACTIVITY_PREFERENCE_CREATED event
            success = self.publisher.publish_preference_created(
                preference_id,
                int(preference.patient_id),
                int(preference.centre_activity_id),
                preference_data,
                "sync_script"
            )
            
            if success:
                self.logger.info(f"Emitted ACTIVITY_PREFERENCE_CREATED event for preference {preference_id} (Patient: {preference.patient_id})")
                return True
            else:
                self.logger.error(f"Failed to emit ACTIVITY_PREFERENCE_CREATED event for preference {preference_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing preference {getattr(preference, 'id', 'unknown')}: {str(e)}")
            raise
    
    def _preference_to_dict(self, preference) -> Dict[str, Any]:
        """Convert preference model to dictionary for messaging"""
        try:
            preference_dict = {}
            
            # Get all preference attributes
            for column in preference.__table__.columns:
                value = getattr(preference, column.name)
                
                # Convert datetime objects to ISO format strings
                if hasattr(value, 'isoformat'):
                    preference_dict[column.name] = value.isoformat()
                else:
                    preference_dict[column.name] = value
            
            return preference_dict
            
        except Exception as e:
            self.logger.error(f"Error converting preference to dict: {str(e)}")
            return {}


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Emit ACTIVITY_PREFERENCE_UPDATED events for existing activity preferences')
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual events emitted)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of preferences to process per batch (default: 100)')
    
    args = parser.parse_args()
    
    try:
        # Create and run the script
        script = ActivityPreferenceSyncScript(
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

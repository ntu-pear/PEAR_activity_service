import sys
import os
import argparse
from typing import List, Optional, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from .base_script import BaseScript

class ActivityExclusionSyncScript(BaseScript):
    """
    Script to emit EXCLUSION_CREATED events for existing activity exclusions in the database
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
            from app.models.centre_activity_exclusion_model import CentreActivityExclusion
            
            # Import messaging dependencies  
            from messaging.activity_exclusion_publisher import get_activity_exclusion_publisher
            
            # Set up database
            engine = create_engine(get_database_url())
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.CentreActivityExclusion = CentreActivityExclusion
            self.func = func
            
            # Set up messaging
            self.publisher = get_activity_exclusion_publisher()
            
            self.logger.info("Dependencies initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dependencies: {str(e)}")
            raise
    
    def get_total_count(self) -> int:
        """Get total number of activity exclusions in the database"""
        try:
            with self.SessionLocal() as db:
                # Count exclusions
                count = db.query(self.func.count(self.CentreActivityExclusion.id)).scalar()
                
                self.logger.info(f"Found {count} exclusions in database")
                return count
                
        except Exception as e:
            self.logger.error(f"Error getting exclusion count: {str(e)}")
            raise
    
    def fetch_batch(self, offset: int, limit: int) -> List[Any]:
        """Fetch a batch of exclusions from the database"""
        try:
            with self.SessionLocal() as db:
                exclusions = db.query(self.CentreActivityExclusion).order_by(self.CentreActivityExclusion.id).offset(offset).limit(limit).all()
                
                self.logger.debug(f"Fetched {len(exclusions)} exclusions from offset {offset}")
                return exclusions
                
        except Exception as e:
            self.logger.error(f"Error fetching exclusion batch: {str(e)}")
            raise
    
    def process_item(self, exclusion) -> bool:
        """Process a single exclusion - emit ACTIVITY_EXCLUSION_CREATED event"""
        try:
            exclusion_id = exclusion.id
            
            # Convert exclusion model to dictionary
            exclusion_data = self._exclusion_to_dict(exclusion)
            
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would emit ACTIVITY_EXCLUSION_CREATED for exclusion {exclusion_id} (Patient: {exclusion.patient_id})")
                self.logger.debug(f"Exclusion data: {exclusion_data}")
                return True
            
            # Emit ACTIVITY_EXCLUSION_CREATED event
            success = self.publisher.publish_exclusion_created(
                exclusion_id,
                int(exclusion.patient_id),
                int(exclusion.centre_activity_id),
                exclusion_data,
                "sync_script"
            )
            
            if success:
                self.logger.info(f"Emitted ACTIVITY_EXCLUSION_CREATED event for exclusion {exclusion_id} (Patient: {exclusion.patient_id})")
                return True
            else:
                self.logger.error(f"Failed to emit ACTIVITY_EXCLUSION_CREATED event for exclusion {exclusion_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing exclusion {getattr(exclusion, 'id', 'unknown')}: {str(e)}")
            raise
    
    def _exclusion_to_dict(self, exclusion) -> Dict[str, Any]:
        """Convert exclusion model to dictionary for messaging"""
        try:
            exclusion_dict = {}
            
            # Get all exclusion attributes
            for column in exclusion.__table__.columns:
                value = getattr(exclusion, column.name)
                
                # Convert datetime objects to ISO format strings
                if hasattr(value, 'isoformat'):
                    exclusion_dict[column.name] = value.isoformat()
                else:
                    exclusion_dict[column.name] = value
            
            return exclusion_dict
            
        except Exception as e:
            self.logger.error(f"Error converting exclusion to dict: {str(e)}")
            return {}


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Emit ACTIVITY_EXCLUSION_CREATED events for existing activity exclusions')
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual events emitted)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of exclusions to process per batch (default: 100)')
    
    args = parser.parse_args()
    
    try:
        # Create and run the script
        script = ActivityExclusionSyncScript(
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

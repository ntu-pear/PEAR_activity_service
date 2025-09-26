import sys
import os
import argparse
from typing import List, Optional, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from .base_script import BaseScript

class ActivityRecommendationSyncScript(BaseScript):
    """
    Script to emit RECOMMENDATION_UPDATED events for existing activity recommendations in the database
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
            
            # Import all models to ensure relationships are properly resolved
            try:
                import models  # This imports all models via __init__.py
                from models.centre_activity_recommendation_model import CentreActivityRecommendation
            except ImportError:
                # Fallback to direct import
                from models.centre_activity_model import CentreActivity  # Import this first
                from models.centre_activity_recommendation_model import CentreActivityRecommendation
            
            # Import messaging dependencies  
            from messaging.activity_recommendation_publisher import get_activity_recommendation_publisher
            
            # Set up database
            engine = create_engine(get_database_url())
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.CentreActivityRecommendation = CentreActivityRecommendation
            self.func = func
            
            # Set up messaging
            self.publisher = get_activity_recommendation_publisher()
            
            self.logger.info("Dependencies initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dependencies: {str(e)}")
            raise
    
    def get_total_count(self) -> int:
        """Get total number of activity recommendations in the database"""
        try:
            with self.SessionLocal() as db:
                # Count recommendations
                count = db.query(self.func.count(self.CentreActivityRecommendation.id)).scalar()
                
                self.logger.info(f"Found {count}  recommendations in database")
                return count
                
        except Exception as e:
            self.logger.error(f"Error getting recommendation count: {str(e)}")
            raise
    
    def fetch_batch(self, offset: int, limit: int) -> List[Any]:
        """Fetch a batch of recommendations from the database"""
        try:
            with self.SessionLocal() as db:
                recommendations = db.query(self.CentreActivityRecommendation).order_by(self.CentreActivityRecommendation.id).offset(offset).limit(limit).all()
                
                self.logger.debug(f"Fetched {len(recommendations)} recommendations from offset {offset}")
                return recommendations
                
        except Exception as e:
            self.logger.error(f"Error fetching recommendation batch: {str(e)}")
            raise
    
    def process_item(self, recommendation) -> bool:
        """Process a single recommendation - emit ACTIVITY_RECOMMENDATION_CREATED event"""
        try:
            recommendation_id = recommendation.id
            
            # Convert recommendation model to dictionary
            recommendation_data = self._recommendation_to_dict(recommendation)
            
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would emit ACTIVITY_RECOMMENDATION_CREATED for recommendation {recommendation_id} (Patient: {recommendation.patient_id})")
                self.logger.debug(f"Recommendation data: {recommendation_data}")
                return True
            
            # Emit ACTIVITY_RECOMMENDATION_CREATED event
            success = self.publisher.publish_recommendation_created(
                recommendation_id,
                int(recommendation.patient_id),
                int(recommendation.centre_activity_id),
                str(recommendation.doctor_id),
                recommendation_data,
                "sync_script"
            )
            
            if success:
                self.logger.info(f"Emitted ACTIVITY_RECOMMENDATION_CREATED event for recommendation {recommendation_id} (Patient: {recommendation.patient_id})")
                return True
            else:
                self.logger.error(f"Failed to emit ACTIVITY_RECOMMENDATION_CREATED event for recommendation {recommendation_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing recommendation {getattr(recommendation, 'id', 'unknown')}: {str(e)}")
            raise
    
    def _recommendation_to_dict(self, recommendation) -> Dict[str, Any]:
        """Convert recommendation model to dictionary for messaging"""
        try:
            recommendation_dict = {}
            
            # Get all recommendation attributes
            for column in recommendation.__table__.columns:
                value = getattr(recommendation, column.name)
                
                # Convert datetime objects to ISO format strings
                if hasattr(value, 'isoformat'):
                    recommendation_dict[column.name] = value.isoformat()
                else:
                    recommendation_dict[column.name] = value
            
            return recommendation_dict
            
        except Exception as e:
            self.logger.error(f"Error converting recommendation to dict: {str(e)}")
            return {}


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Emit RECOMMENDATION_UPDATED events for existing activity recommendations')
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual events emitted)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of recommendations to process per batch (default: 100)')
    
    args = parser.parse_args()
    
    try:
        # Create and run the script
        script = ActivityRecommendationSyncScript(
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

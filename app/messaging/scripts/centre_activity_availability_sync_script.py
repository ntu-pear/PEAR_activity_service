import sys
import os
import argparse
from typing import List, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from .base_script import BaseScript

class CentreActivityAvailabilitySyncScript(BaseScript):
    """
    Script to emit CENTRE_ACTIVITY_AVAILABILITY_CREATED events for existing availabilities in the database.
    Events are flagged as sync events so the scheduler upserts them even if they were sent before.
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
            from app.models.centre_activity_availability_model import CentreActivityAvailability

            # Import messaging dependencies
            from messaging.centre_activity_availability_publisher import get_centre_activity_availability_publisher

            # Set up database
            engine = create_engine(get_database_url())
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.CentreActivityAvailability = CentreActivityAvailability
            self.func = func

            # Set up messaging
            self.publisher = get_centre_activity_availability_publisher()

            self.logger.info("Dependencies initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize dependencies: {str(e)}")
            raise

    def get_total_count(self) -> int:
        """Get total number of availabilities in the database (including soft-deleted)"""
        try:
            with self.SessionLocal() as db:
                count = db.query(self.func.count(self.CentreActivityAvailability.id)).scalar()

                self.logger.info(f"Found {count} centre activity availabilities in database")
                return count

        except Exception as e:
            self.logger.error(f"Error getting availability count: {str(e)}")
            raise

    def fetch_batch(self, offset: int, limit: int) -> List[Any]:
        """Fetch a batch of availabilities from the database"""
        try:
            with self.SessionLocal() as db:
                availabilities = (
                    db.query(self.CentreActivityAvailability)
                    .order_by(self.CentreActivityAvailability.id)
                    .offset(offset)
                    .limit(limit)
                    .all()
                )

                self.logger.debug(f"Fetched {len(availabilities)} availabilities from offset {offset}")
                return availabilities

        except Exception as e:
            self.logger.error(f"Error fetching availability batch: {str(e)}")
            raise

    def process_item(self, availability) -> bool:
        """Process a single availability - emit CENTRE_ACTIVITY_AVAILABILITY_CREATED event"""
        try:
            availability_id = availability.id
            availability_data = self._availability_to_dict(availability)

            if self.dry_run:
                self.logger.info(
                    f"[DRY RUN] Would emit CENTRE_ACTIVITY_AVAILABILITY_CREATED for availability {availability_id} "
                    f"(Centre activity: {availability.centre_activity_id})"
                )
                self.logger.debug(f"Availability data: {availability_data}")
                return True

            success = self.publisher.publish_availability_created(
                availability_id,
                availability_data,
                "sync_script",
                is_sync_event=True,
                sync_reason="initial_backfill",
            )

            if success:
                self.logger.info(
                    f"Emitted CENTRE_ACTIVITY_AVAILABILITY_CREATED event for availability {availability_id} "
                    f"(Centre activity: {availability.centre_activity_id})"
                )
                return True
            else:
                self.logger.error(f"Failed to emit CENTRE_ACTIVITY_AVAILABILITY_CREATED event for availability {availability_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error processing availability {getattr(availability, 'id', 'unknown')}: {str(e)}")
            raise

    def _availability_to_dict(self, availability) -> Dict[str, Any]:
        """Convert availability model to dictionary for messaging (columns only)"""
        try:
            availability_dict = {}

            for column in availability.__table__.columns:
                value = getattr(availability, column.name)

                # Convert date/time objects to ISO format strings
                if hasattr(value, 'isoformat'):
                    availability_dict[column.name] = value.isoformat()
                else:
                    availability_dict[column.name] = value

            return availability_dict

        except Exception as e:
            self.logger.error(f"Error converting availability to dict: {str(e)}")
            return {}


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Emit CENTRE_ACTIVITY_AVAILABILITY_CREATED events for existing centre activity availabilities')

    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual events emitted)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of availabilities to process per batch (default: 100)')

    args = parser.parse_args()

    try:
        script = CentreActivityAvailabilitySyncScript(
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

# This script is used to test the logging functionality of the application.
# Run this script to generate log entries for CREATE, UPDATE, and DELETE actions.
# "python -m scripts.test_logger"

import os
import sys
from datetime import datetime
from app.logger.logger_utils import log_crud_action, ActionType

if __name__ == "__main__":
    # Test CREATE action
    log_crud_action(
        action=ActionType.CREATE,
        user="testuser",
        user_full_name="Test User",
        message="Created a new entity.",
        table="TestTable",
        entity_id=1,
        original_data=None,
        updated_data={"name": "Test Entity", "CreatedDate": datetime.now(), "CreatedById": 123, "value": 42}
    )

    # Test UPDATE action
    log_crud_action(
        action=ActionType.UPDATE,
        user="testuser",
        user_full_name="Test User",
        message="Updated an entity.",
        table="TestTable",
        entity_id=1,
        original_data={"name": "Old Name", "ModifiedDate": datetime.now(), "ModifiedById": 123, "value": 41},
        updated_data={"name": "New Name", "ModifiedDate": datetime.now(), "ModifiedById": 123, "value": 42}
    )

    # Test DELETE action
    log_crud_action(
        action=ActionType.DELETE,
        user="testuser",
        user_full_name="Test User",
        message="Deleted an entity.",
        table="TestTable",
        entity_id=1,
        original_data={"name": "To Be Deleted", "IsDeleted": True, "value": 42},
        updated_data=None
    )

    print("Logger test completed. Check your log files for output.")

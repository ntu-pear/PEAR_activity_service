from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import json

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
log_file = f"{LOG_DIR}/activity_{today}.log"

class ConditionalFormatter(logging.Formatter):
    """
    Emits real JSON (via json.dumps) instead of %-style string
    interpolation, so missing/None fields serialize as JSON null rather
    than the literal string "None" -- the logger service's LogDocument
    schema can't coerce "None" into Optional[int] fields like patient_id,
    which was silently dropping every log for patient-independent tables
    (ACTIVITY, CARE_CENTRE, CENTRE_ACTIVITY_AVAILABILITY, ...).
    """
    def format(self, record):
        timestamp = self.formatTime(record, self.datefmt)
        if all(hasattr(record, f) for f in ["user", "user_full_name", "table", "action", "log_text"]):
            log_dict = {
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name,
                "user": record.user,
                "user_full_name": record.user_full_name,
                "table": record.table,
                "action": record.action,
                "log_text": record.log_text,
                "patient_id": getattr(record, "patient_id", None),
                "patient_full_name": getattr(record, "patient_full_name", None),
                "log_type": getattr(record, "log_type", None),
                "is_system_config": bool(getattr(record, "is_system_config", False)),
                "message": record.msg,
            }
        else:
            log_dict = {
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
        return json.dumps(log_dict, default=str)

date_format = "%Y-%m-%dT%H:%M:%S"

# Create custom formatter
custom_formatter = ConditionalFormatter(datefmt=date_format)

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(custom_formatter)

# Also add console handler for debugging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only show warnings and errors in console
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
))

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

logger = logging.getLogger(__name__)

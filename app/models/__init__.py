# Import all models to ensure they are registered with SQLAlchemy
from .activity_model import Activity
from .care_centre_model import CareCentre
from .centre_activity_model import CentreActivity
from .centre_activity_availability_model import CentreActivityAvailability
from .centre_activity_exclusion_model import CentreActivityExclusion
from .centre_activity_preference_model import CentreActivityPreference
from .centre_activity_recommendation_model import CentreActivityRecommendation
from .adhoc_model import Adhoc
from .outbox_model import OutboxEvent

# Export all models
__all__ = [
    'Activity',
    'CareCentre', 
    'CentreActivity',
    'CentreActivityAvailability',
    'CentreActivityExclusion',
    'CentreActivityPreference',
    'CentreActivityRecommendation',
    'Adhoc',
    'OutboxEvent'
]

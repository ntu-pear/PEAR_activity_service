from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey
from datetime import datetime, date
from app.database import Base


class ActivityTemplate(Base):
    """A blank activity form, saved for reuse.

    A template is not an activity. Saving one writes this row and nothing else -
    no Activity, no CentreActivity, no event, and the Scheduler never hears about
    it. Applying a template is what creates data, and it leaves this row
    untouched so the same template can be applied again.

    The field set is the union of what ACTIVITY and CENTRE_ACTIVITY hold, minus
    activity_id, which does not exist until a template is applied. `name` is the
    one field that belongs to the template itself rather than to the rows it
    produces: it labels the template in the list, so two templates producing
    similarly titled activities can be told apart.
    """
    __tablename__ = "ACTIVITY_TEMPLATE"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Names the template, not the activity it produces.
    name = Column(String(200), nullable=False)

    # Become the ACTIVITY row
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)

    # Become the CENTRE_ACTIVITY row
    care_centre_id = Column(Integer, ForeignKey("CARE_CENTRE.id"), nullable=True)
    is_compulsory = Column(Boolean, nullable=False, default=True)
    is_fixed = Column(Boolean, nullable=False, default=False)
    is_group = Column(Boolean, nullable=False, default=False)
    start_date = Column(Date, nullable=False, default=date.today)
    end_date = Column(Date, nullable=False, default=date(2999, 1, 1))
    min_duration = Column(Integer, nullable=False, default=60)
    max_duration = Column(Integer, nullable=False, default=60)
    min_people_req = Column(Integer, nullable=False, default=1)
    fixed_time_slots = Column(String, nullable=True)

    is_deleted = Column(Boolean, nullable=False, default=False)

    created_date = Column(DateTime, nullable=False, default=datetime.now)
    modified_date = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)
    created_by_id = Column(String(50), nullable=False)
    modified_by_id = Column(String(50), nullable=True)

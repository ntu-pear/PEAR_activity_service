from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base

class CentreActivity(Base):
    __tablename__ = "CENTRE_ACTIVITY"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, ForeignKey("ACTIVITY.id"), nullable=False)

    # What this configuration is called, e.g. "Breathing AM" and "Breathing PM"
    # under one "Breathing" activity. Without it the only name a centre activity
    # has is its parent activity's title, so two variants have to be two
    # separate activities.
    #
    # Nullable because rows created before this column existed have no name;
    # read it as `name or activity.title`. Tighten to nullable=False once every
    # environment has been backfilled.
    name = Column(String(200), nullable=True)

    # Nullable because rows created before this column existed have no centre.
    # Tighten to nullable=False once every environment has been backfilled.
    care_centre_id = Column(Integer, ForeignKey("CARE_CENTRE.id"), nullable=True)

    is_deleted = Column(Boolean, nullable=False, default=False)
    is_compulsory = Column(Boolean, nullable=False, default=True)
    is_fixed = Column(Boolean, nullable=False, default=False)
    is_group = Column(Boolean, nullable=False, default=False)

    start_date = Column(Date, nullable=False, default=date.today())
    end_date = Column(Date, nullable=False, default=date(2999, 1, 1))       # Indefinite end date will be far in the future instead of null
    
    # Duration will only be 60min to make it easy for Scheduler.
    # Will still keep these fields in case future allows diff durations
    min_duration = Column(Integer, nullable=False, default=30)       
    max_duration = Column(Integer, nullable=False, default =30)
    min_people_req = Column(Integer, nullable=False, default=1)
    fixed_time_slots = Column(String, nullable=True)

    created_date = Column(DateTime, nullable=False, default=datetime.now)
    modified_date = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)
    created_by_id = Column(String, nullable=False)
    modified_by_id = Column(String, nullable=True)

    activity = relationship("Activity", lazy="joined")
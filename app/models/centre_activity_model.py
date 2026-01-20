from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base

class CentreActivity(Base):
    __tablename__ = "CENTRE_ACTIVITY"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, ForeignKey("ACTIVITY.id"), nullable=False)

    is_deleted = Column(Boolean, nullable=False, default=False)
    is_compulsory = Column(Boolean, nullable=False, default=True)
    is_fixed = Column(Boolean, nullable=False, default=False)
    is_group = Column(Boolean, nullable=False, default=False)

    start_date = Column(Date, nullable=False, default=date.today())
    end_date = Column(Date, nullable=False, default=date(2999, 1, 1))       # Indefinite end date will be far in the future instead of null
    
    # Duration will only be 60min to make it easy for Scheduler.
    # Will still keep these fields in case future allows diff durations
    min_duration = Column(Integer, nullable=False, default=60)       
    max_duration = Column(Integer, nullable=False, default =60)
    min_people_req = Column(Integer, nullable=False, default=1)
    fixed_time_slots = Column(String, nullable=True)

    created_date = Column(DateTime, nullable=False, default=datetime.now)
    modified_date = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)
    created_by_id = Column(String, nullable=False)
    modified_by_id = Column(String, nullable=True)

    activity = relationship("Activity")
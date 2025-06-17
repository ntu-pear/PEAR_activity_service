from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class CentreActivity(Base):
    __tablename__ = "CENTRE_ACTIVITY"

    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Integer, nullable=False, default=1)
    activity_id = Column(Integer, ForeignKey("ACTIVITY.id"), nullable=False)

    is_deleted = Column(Boolean, nullable=False, default=False)
    is_compulsory = Column(Boolean, nullable=False, default=True)
    is_fixed = Column(Boolean, nullable=False, default=False)
    is_group = Column(Boolean, nullable=False, default=False)

    min_duration = Column(Integer, nullable=False, default=30)  
    max_duration = Column(Integer, nullable=False, default =60)
    min_people_req = Column(Integer, nullable=False, default=1)
    fixed_time_slots = Column(String, nullable=True)

    created_date = Column(DateTime, nullable=False, default=datetime.now())
    modified_date = Column(DateTime, nullable=False, default=datetime.now(), onupdate=datetime.utcnow)
    created_by_id = Column(String, nullable=False)
    modified_by_id = Column(String, nullable=False)

    activity = relationship("Activity")
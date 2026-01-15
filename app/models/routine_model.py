from sqlalchemy import Column, Integer, Boolean, DateTime, Time, Date, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Routine(Base):
    __tablename__ = "ROUTINE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    activity_id = Column(Integer, ForeignKey("ACTIVITY.id"), nullable=False)
    patient_id = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_date = Column(DateTime, nullable=False, default=datetime.now())
    modified_date = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)
    created_by_id = Column(Integer, nullable=False)
    modified_by_id = Column(Integer, nullable=True)

    activity = relationship("Activity", foreign_keys=[activity_id])

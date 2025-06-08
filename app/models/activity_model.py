import uuid, datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime
from app.utils.database import Base

class Activity(Base):
    __tablename__ = "activity"

    id                  = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title               = Column(String, nullable=False)
    description         = Column(String, nullable=True)
    start_date          = Column(DateTime, nullable=False)
    end_date            = Column(DateTime, nullable=True)
    is_fixed            = Column(Boolean, default=False)
    is_compulsory       = Column(Boolean, default=False)
    is_group            = Column(Boolean, default=False)
    min_duration        = Column(Integer, nullable=True)
    max_duration        = Column(Integer, nullable=True)
    min_people_required = Column(Integer, nullable=True)
    created_date        = Column(DateTime, default=datetime.datetime.utcnow)
    modified_date       = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
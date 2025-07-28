from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class CentreActivityPreference(Base):
    __tablename__ = "CENTRE_ACTIVITY_PREFERENCE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    centre_activity_id = Column(Integer, ForeignKey("CENTRE_ACTIVITY.id"), nullable=False)
    patient_id = Column(Integer, nullable=False)    # Foreign key to Patient table

    is_like = Column(Boolean, nullable=False, default=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    created_date = Column(DateTime, nullable=False, default=datetime.now())
    modified_date = Column(DateTime, nullable=True, onupdate=datetime.now())
    created_by_id = Column(String, nullable=False)
    modified_by_id = Column(String, nullable=True)

    centre_activity = relationship("CentreActivity")
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class CentreActivityRecommendation(Base):
    __tablename__ = "CENTRE_ACTIVITY_RECOMMENDATION"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    centre_activity_id = Column(Integer, ForeignKey("CENTRE_ACTIVITY.id"), nullable=False)
    patient_id = Column(Integer, nullable=False)  # Foreign key to external db
    doctor_id = Column(Integer, nullable=False)  # Foreign key to external db

    doctor_recommendation = Column(Integer, nullable=False)     #-1 (Not recommended), 0 (Neutral), 1 (Recommended)
    doctor_remarks = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    created_date = Column(DateTime, nullable=False, default=datetime.now)
    modified_date = Column(DateTime, nullable=True, default=None, onupdate=datetime.utcnow)
    created_by_id = Column(String, nullable=False)
    modified_by_id = Column(String, nullable=True)

    centre_activity = relationship("CentreActivity", foreign_keys=[centre_activity_id])

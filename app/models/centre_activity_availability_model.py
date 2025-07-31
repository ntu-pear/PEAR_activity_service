from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class CentreActivityAvailability(Base):
    __tablename__ = "CENTRE_ACTIVITY_AVAILABILITY"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    centre_activity_id = Column(Integer, ForeignKey("CENTRE_ACTIVITY.id"), nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    start_time = Column(DateTime, nullable=False, default=None)
    end_time = Column(DateTime, nullable=False, default=None)
    created_date = Column(DateTime, nullable=False, default=datetime.now())
    modified_date = Column(DateTime, nullable=True, default=None, onupdate=datetime.now(timezone.utc))
    created_by_id = Column(String, nullable=False)
    modified_by_id = Column(String, nullable=True)

    centre_activity = relationship("CentreActivity")

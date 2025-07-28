from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Adhoc(Base):
    __tablename__ = "ADHOC"

    id = Column(Integer, primary_key=True, autoincrement=True)
    old_centre_activity_id = Column(
        Integer,
        ForeignKey("CENTRE_ACTIVITY.id"),
        nullable=False
    )
    new_centre_activity_id = Column(
        Integer,
        ForeignKey("CENTRE_ACTIVITY.id"),
        nullable=False
    )

    is_deleted = Column(Boolean, nullable=False, default=False)
    status = Column(String, nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time   = Column(DateTime, nullable=False)

    created_date  = Column(DateTime, nullable=False, default=datetime.now())
    modified_date = Column(DateTime, nullable=True, default=None, onupdate=datetime.utcnow)

    created_by_id  = Column(String, nullable=False)
    modified_by_id = Column(String, nullable=True)

    # relationships back to centre_activity
    old_activity = relationship("CentreActivity", foreign_keys=[old_centre_activity_id])
    new_activity = relationship("CentreActivity", foreign_keys=[new_centre_activity_id])
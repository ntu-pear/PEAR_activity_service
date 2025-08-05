from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class ActivityExclusion(Base):
    __tablename__ = "ACTIVITY_EXCLUSION"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    activity_id       = Column(Integer, ForeignKey("ACTIVITY.id"), nullable=False)
    patient_id        = Column(Integer, nullable=False)
    is_deleted        = Column(Boolean, nullable=False, default=False)
    exclusion_remarks = Column(String,  nullable=True)
    start_date        = Column(Date,    nullable=False)
    end_date          = Column(Date,    nullable=True)
    created_date      = Column(DateTime, nullable=False, server_default=func.sysutcdatetime())
    modified_date     = Column(DateTime, nullable=False,
                                server_default=func.sysutcdatetime(),
                                onupdate=func.sysutcdatetime())
    created_by_id     = Column(String(50), nullable=True)
    modified_by_id    = Column(String(50), nullable=True)

    # relationship back to Activity
    activity = relationship("Activity", lazy="joined")
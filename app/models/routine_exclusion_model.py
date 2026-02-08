from sqlalchemy import Column, Integer, Boolean, DateTime, Date, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class RoutineExclusion(Base):
    __tablename__ = "ROUTINE_EXCLUSION"

    id = Column(Integer, primary_key=True, autoincrement=True)
    routine_id = Column(Integer, ForeignKey("ROUTINE.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    remarks = Column(String, nullable=True)
    created_date = Column(DateTime, nullable=False, default=datetime.now)
    modified_date = Column(DateTime, nullable=True, default=None, onupdate=datetime.now)
    created_by_id = Column(String(50), nullable=False)
    modified_by_id = Column(String(50), nullable=True)

    routine = relationship("Routine", foreign_keys=[routine_id])

from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class RefPatient(Base):
    __tablename__ = "REF_PATIENT"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(255), nullable=False)
    preferred_name = Column("preferred_name", String(255), nullable=True)
    update_bit = Column("update_bit", String(1), default="1", nullable=False)
    start_date = Column("start_date", DateTime, nullable=False)
    end_date = Column("end_date", DateTime, nullable=True)
    is_active = Column("is_active", String(1), default="1", nullable=False)
    is_deleted = Column("is_deleted", String(1), default="0", nullable=False)
    
    created_date = Column("created_date", DateTime, nullable=False,
                          server_default=func.sysutcdatetime())
    modified_date = Column("modified_date", DateTime, nullable=False,
                           server_default=func.sysutcdatetime(),
                           onupdate=func.sysutcdatetime())
    created_by_id = Column("created_by_id", String(50), nullable=True)
    modified_by_id = Column("modified_by_id", String(50), nullable=True)

    allocations = relationship("RefPatientAllocation", back_populates="patient")

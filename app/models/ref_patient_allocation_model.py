from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone


class RefPatientAllocation(Base):
    __tablename__ = "REF_PATIENT_ALLOCATION"

    id = Column(Integer, primary_key=True, index=True)
    active = Column(String(1), default='Y', nullable=False)
    isDeleted = Column(String(1), default='0', nullable=False)
    patientId = Column(Integer, ForeignKey('REF_PATIENT.id'))
    doctorId = Column(String, nullable=False)
    gameTherapistId = Column(String, nullable=False)
    supervisorId = Column(String, nullable=False)
    caregiverId = Column(String, nullable=False)
    tempDoctorId = Column(String)
    tempCaregiverId = Column(String)

    created_date  = Column("created_date", DateTime, nullable=False,
                           server_default=func.sysutcdatetime())
    modified_date = Column("modified_date", DateTime, nullable=False,
                           server_default=func.sysutcdatetime(),
                           onupdate=func.sysutcdatetime())
    created_by_id  = Column("created_by_id", String(50), nullable=True)
    modified_by_id = Column("modified_by_id", String(50), nullable=True)    

    patient = relationship("RefPatient", back_populates="allocations")

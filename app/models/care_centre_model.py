from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time
from datetime import datetime
from app.database import Base

class CareCentre(Base):
    __tablename__ = "CARE_CENTRE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)

    country_code = Column(String(3), nullable=False)            # ISO 3166-1 alpha-3 country code
    address = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)

    contact_no = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    no_of_devices_avail = Column(Integer, nullable=False, default=0)

    # To be reconsidered
    working_day = Column(String(50), nullable=True)           
    opening_hours = Column(Time, nullable=True)      
    closing_hours = Column(Time, nullable=True)     
    #====
    remarks = Column(String(255), nullable=True)

    created_date = Column(DateTime, nullable=False, default=datetime.now())
    modified_date = Column(DateTime, nullable=False, default=datetime.now(), onupdate=datetime.utcnow)
    created_by_id = Column(String(50), nullable=True)
    modified_by_id = Column(String(50), nullable=True)

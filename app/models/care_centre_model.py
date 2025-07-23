from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, JSON
from datetime import datetime
from app.database import Base

class CareCentre(Base):
    __tablename__ = "CARE_CENTRE"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)

    country_code = Column(String(3), nullable=False)            # ISO 3166-1 alpha-3 country code
    address = Column(String(255), nullable=False)
    postal_code = Column(String(6), nullable=False)

    contact_no = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    no_of_devices_avail = Column(Integer, nullable=False, default=0)

    working_hours = Column(JSON, nullable=False, default={
        "monday": {"open": "09:00", "close": "17:00"},
        "tuesday": {"open": "09:00", "close": "17:00"},
        "wednesday": {"open": "09:00", "close": "17:00"},
        "thursday": {"open": "09:00", "close": "17:00"},
        "friday": {"open": "09:00", "close": "17:00"},
        "saturday": {"open": None, "close": None},          
        "sunday": {"open": None, "close": None}             
    })

    remarks = Column(String(255), nullable=True)

    created_date = Column(DateTime, nullable=False, default=datetime.now)
    modified_date = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)
    created_by_id = Column(String(50), nullable=False)
    modified_by_id = Column(String(50), nullable=True)

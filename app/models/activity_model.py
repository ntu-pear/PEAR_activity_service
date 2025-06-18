from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base

class Activity(Base):
    __tablename__ = "ACTIVITY"

    id            = Column("id", Integer, primary_key=True, autoincrement=True)
    active        = Column("active", Boolean, nullable=False, default=True)
    is_deleted    = Column("is_deleted", Boolean, nullable=False, default=False) 
    title         = Column("title", String(200), nullable=False)
    description   = Column("description", String, nullable=True)
    start_date    = Column("start_date", DateTime, nullable=False)
    end_date      = Column("end_date", DateTime, nullable=True)
    created_date  = Column("created_date", DateTime, nullable=False,
                           server_default=func.sysutcdatetime())
    modified_date = Column("modified_date", DateTime, nullable=False,
                           server_default=func.sysutcdatetime(),
                           onupdate=func.sysutcdatetime())
    created_by_id  = Column("created_by_id", String(50), nullable=True)
    modified_by_id = Column("modified_by_id", String(50), nullable=True)    
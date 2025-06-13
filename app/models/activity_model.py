from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base

class Activity(Base):
    __tablename__ = "ACTIVITY"

    id            = Column("ID", Integer, primary_key=True, autoincrement=True)
    active        = Column("ACTIVE", Boolean, nullable=False, default=True)
    is_deleted    = Column("IS_DELETED", Boolean, nullable=False, default=False) 
    title         = Column("TITLE", String(200), nullable=False)
    description   = Column("DESCRIPTION", String, nullable=True)
    startDate    = Column("START_DATE", DateTime, nullable=False)
    endDate      = Column("END_DATE", DateTime, nullable=True)
    created_date  = Column("CREATED_DATE", DateTime, nullable=False,
                           server_default=func.sysutcdatetime())
    modified_date = Column("MODIFIED_DATE", DateTime, nullable=False,
                           server_default=func.sysutcdatetime(),
                           onupdate=func.sysutcdatetime())
    created_by_id  = Column("CREATED_BY_ID", String(50), nullable=True)
    modified_by_id = Column("MODIFIED_BY_ID", String(50), nullable=True)    
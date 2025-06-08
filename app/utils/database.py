from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# adjust this URL to your real database ###not yet implemented###
SQLALCHEMY_DATABASE_URL = "sqlite:///./dev.db"

# for SQLite only
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# this is what your models.Base should point to
Base = declarative_base()

# dependency you already use in routers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
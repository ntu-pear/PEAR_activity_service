import os
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()       

#==== General Server Connection Config===
DB_DRIVER_DEV = os.getenv("DB_DRIVER_DEV")
if not DB_DRIVER_DEV:
    raise ValueError("DB_DRIVER_DEV environment variable is not set.")

DB_SERVER_DEV = os.getenv("DB_SERVER_DEV")
if not DB_SERVER_DEV:
    raise ValueError("DB_SERVER_DEV environment variable is not set.")

DB_DATABASE_PORT = os.getenv("DB_DATABASE_PORT")
if not DB_DATABASE_PORT:
    raise ValueError("DB_DATABASE_PORT environment variable is not set.")

#====  DB Connection Config ===
DB_DATABASE_DEV = os.getenv("DB_DATABASE_DEV")
if not DB_DATABASE_DEV:
    raise ValueError("DB_DATABASE_DEV environment variable is not set.")

DB_USERNAME_DEV = os.getenv("DB_USERNAME_DEV")
if not DB_USERNAME_DEV:
    raise ValueError("DB_USERNAME_DEV environment variable is not set.")

DB_PASSWORD_DEV = os.getenv("DB_PASSWORD_DEV")
if not DB_PASSWORD_DEV:
    raise ValueError("DB_PASSWORD_DEV environment variable is not set.")
#====


##### Note that this connection is to the DEV environment ####
# COMMMENT out this section when doing local development
# OR change your env var accordingly to point to your db
connection_url = sa.URL.create(
    "mssql+pyodbc",
    database=DB_DATABASE_DEV,
    username=DB_USERNAME_DEV,
    password=DB_PASSWORD_DEV,
    host=DB_SERVER_DEV,
    port=DB_DATABASE_PORT,
    query={"driver": DB_DRIVER_DEV, "TrustServerCertificate": "yes"},
)

###############################################################
# Get the database URL from environment (DOCKER LOCAL)
DB_URL_LOCAL = os.getenv("DB_URL_LOCAL")
DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

#===== Local Docker Development =========
# connection_url = sa.URL.create(
#     "mssql+pyodbc",
#     username=DB_USERNAME,
#     password=DB_PASSWORD,
#     host=DB_SERVER,
#     port=DB_DATABASE_PORT,
#     database=DB_DATABASE,
#     query={"driver": DB_DRIVER, "TrustServerCertificate": "yes"},
# )
##############################################

print(connection_url)
engine = sa.create_engine(connection_url)
##############################################################
# print(DATABASE_URL)
# engine = create_engine(DATABASE_URL, connect_args={"timeout": 30})
# engine_dev = create_engine(DATABASE_URL_DEV, )  # Increase the timeout if necessary

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models. All ORM models should inherit from this.
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
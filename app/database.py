import os
import sys
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()       


#===== Service Env Var Check======
SERVICE_NAME = os.getenv("SERVICE_NAME")
if SERVICE_NAME != "ACTIVITY":
    print("Please ensure you are using the correct .env file for ACTIVITY service!")
    sys.exit(1)


#====  DB Connection Config ===
def get_env_var(name, required=True, service=None):
    value = os.getenv(name)
    if required and not value:
        print(f"{name} environment variable is not set.")
        sys.exit(1)
    return value

DB_DRIVER = get_env_var("DB_DRIVER")
DB_SERVER = get_env_var("DB_SERVER")
DB_DATABASE_PORT = get_env_var("DB_DATABASE_PORT")
DB_DATABASE = get_env_var("DB_DATABASE")
DB_USERNAME = get_env_var("DB_USERNAME")
DB_PASSWORD = get_env_var("DB_PASSWORD")


##### Note that this connection is to the DEV environment ####
# CHANGE your env var accordingly to point to your db
connection_url = sa.URL.create(
    "mssql+pyodbc",
    database=DB_DATABASE,
    username=DB_USERNAME,
    password=DB_PASSWORD,
    host=DB_SERVER,
    port=DB_DATABASE_PORT,
    query={"driver": DB_DRIVER, "TrustServerCertificate": "yes"},
)

###############################################################
# Get the database URL from environment (DOCKER LOCAL)
#DB_URL_LOCAL = os.getenv("DB_URL_LOCAL")
#DB_DRIVER = os.getenv("DB_DRIVER")
#DB_SERVER = os.getenv("DB_SERVER")
#DB_DATABASE = os.getenv("DB_DATABASE")
#DB_USERNAME = os.getenv("DB_USERNAME")
#DB_PASSWORD = os.getenv("DB_PASSWORD")

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

def get_database_url():
    return connection_url

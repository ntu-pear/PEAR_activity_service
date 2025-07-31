import logging
import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError  # For handling database-related errors
from .database import engine, Base

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.models import(
    activity_model,
    centre_activity_model,
    care_centre_model,
    centre_activity_preference_model,
    centre_activity_availability_model
)

from app.routers import(
    centre_activity_router,
    activity_router,
    care_centre_router,
    centre_activity_preference_router,
    centre_activity_availability_router
)

API_VERSION_PREFIX = "/api/v1"

load_dotenv()

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="NTU FYP ACTIVITY SERVICE",
    description="This is the Activity service api docs",
    version="1.0.0",
    servers=[],
)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5173",
    os.getenv("WEB_FE_ORIGIN"),
    os.getenv("PATIENT_BE_ORIGIN"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in origins if o],  # filter out None
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error at {request.url}: {exc.errors()}")
    errors = exc.errors()
    for error in errors:
        if "ctx" in error and "error" in error["ctx"]:
            error["ctx"]["error"] = str(error["ctx"]["error"])
    return JSONResponse(
        status_code=400,
        content={"detail": errors, "body": exc.body},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error at {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact the server admin."},
    )

# Database setup
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
except Exception as db_init_error:
    logger.error(f"Failed to initialize database: {str(db_init_error)}", exc_info=True)


# Include routers
routers = [
    (centre_activity_router.router, f"{API_VERSION_PREFIX}/centre_activities", ["Centre Activities"]),
    (activity_router.router, f"{API_VERSION_PREFIX}/activities", ["Activities"]),
    (care_centre_router.router, f"{API_VERSION_PREFIX}/care_centres", ["Care Centres"]),
    (centre_activity_preference_router.router, f"{API_VERSION_PREFIX}/centre_activity_preferences", ["Centre Activity Preferences"]),
    (centre_activity_availability_router.router, f"{API_VERSION_PREFIX}/centre_activity_availabilities", ["Centre Activity Availabilities"])
]

for router, prefix, tags, in routers:
    app.include_router(router, prefix=prefix, tags=tags)


@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the NTU FYP ACTIVITY SERVICE"}

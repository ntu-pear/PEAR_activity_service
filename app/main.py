import logging
import os
import asyncio
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError  # For handling database-related errors
from .database import engine, Base

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.services.background_processor import get_processor
from app.messaging.consumer_manager import create_activity_consumer_manager

from app.models import(
    activity_model,
    centre_activity_exclusion_model,
    centre_activity_model,
    care_centre_model,
    centre_activity_preference_model,
    centre_activity_recommendation_model,
    adhoc_model,
    outbox_model,
    centre_activity_availability_model,
)

from app.routers import(
    auth_router,
    centre_activity_exclusion_router,
    centre_activity_router,
    activity_router,
    care_centre_router,
    centre_activity_preference_router,
    centre_activity_recommendation_router,
    adhoc_router,
    outbox_router,
    centre_activity_availability_router,
    integrity_router
)


API_VERSION_PREFIX = "/api/v1"

load_dotenv()

logger = logging.getLogger("uvicorn")

# Global consumer manager instance
consumer_manager = None
shutdown_event = threading.Event()


def start_consumers():
    """Start RabbitMQ consumers"""
    global consumer_manager
    
    # Check if messaging is enabled (can be controlled via environment variable)
    enable_messaging = os.getenv('ENABLE_MESSAGING', 'true').lower() == 'true'
    
    if not enable_messaging:
        logger.info("Drift consumer disabled via ENABLE_MESSAGING environment variable")
        return
    
    try:
        logger.info("Starting RabbitMQ drift consumer...")
        consumer_manager = create_activity_consumer_manager()
        
        # Pass shutdown event to consumer manager
        consumer_manager.set_shutdown_event(shutdown_event)
        
        # Start all registered consumers
        consumer_manager.start_all_consumers()
        
        logger.info("Drift consumer started successfully")
        
        # Log consumer status
        status = consumer_manager.get_consumer_status()
        for name, state in status.items():
            logger.info(f"Consumer {name}: {state}")
            
    except Exception as e:
        logger.error(f"Failed to start drift consumer: {str(e)}", exc_info=True)
        # Don't fail the entire application if messaging fails
        logger.warning("Application will continue without drift consumer")


def stop_consumers():
    """Stop RabbitMQ consumers"""
    global consumer_manager
    
    if consumer_manager:
        try:
            logger.info("Stopping RabbitMQ drift consumer...")
            consumer_manager.stop_all_consumers()
            logger.info("Drift consumer stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping drift consumer: {str(e)}")
    else:
        logger.info("No drift consumer to stop")


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    """
    Combined lifespan manager that handles both:
    1. Outbox processor
    2. Drift consumer
    """
    # Startup phase
    logger.info("=== Application Startup ===")
    
    # Start outbox processor
    logger.info("Starting outbox processor...")
    processor = get_processor()
    processor_task = asyncio.create_task(processor.start())
    logger.info("Outbox processor started")
    
    # Start drift consumer
    logger.info("Starting drift consumer...")
    await asyncio.get_event_loop().run_in_executor(None, start_consumers)
    
    try:
        # Application is now running - yield control
        logger.info("=== Application Running ===")
        yield
    finally:
        # Shutdown phase
        logger.info("=== Application Shutdown ===")
        
        # Stop drift consumer first
        logger.info("Stopping drift consumer...")
        shutdown_event.set()
        await asyncio.get_event_loop().run_in_executor(None, stop_consumers)
        logger.info("Drift consumer stopped")
        
        # Stop outbox processor
        logger.info("Stopping outbox processor...")
        await processor.stop()
        if not processor_task.done():
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Outbox processor stopped")


app = FastAPI(
    title="NTU FYP ACTIVITY SERVICE",
    description="This is the Activity service api docs",
    version="1.0.0",
    servers=[],
    lifespan=combined_lifespan,  # Use combined lifespan manager
)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5173",
    os.getenv("WEB_FE_ORIGIN"),
    os.getenv("PATIENT_BE_ORIGIN")
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
    (centre_activity_recommendation_router.router, f"{API_VERSION_PREFIX}/centre_activity_recommendations", ["Centre Activity Recommendations"]),
    (adhoc_router.router, f"{API_VERSION_PREFIX}/adhocs", ["Adhoc Activities"]),
    (centre_activity_exclusion_router.router, f"{API_VERSION_PREFIX}/centre_activity_exclusions", ["Centre Activity Exclusions"]),
    (centre_activity_availability_router.router, f"{API_VERSION_PREFIX}/centre_activity_availabilities", ["Centre Activity Availabilities"]),
    (integrity_router.router, f"{API_VERSION_PREFIX}/integrity", ["Integrity"]),
]

# Add auth router separately (without API version prefix for OAuth2 compatibility)
app.include_router(auth_router.router, tags=["Authentication"])

# Add outbox router
app.include_router(outbox_router.router)

for router, prefix, tags, in routers:
    app.include_router(router, prefix=prefix, tags=tags)


@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the NTU FYP ACTIVITY SERVICE"}


@app.get("/health")
def health_check():
    """Health check endpoint that includes consumer status"""
    global consumer_manager
    
    health_status = {
        "status": "healthy",
        "database": "connected",
        "outbox_processor": "unknown",
        "drift_consumer": "unknown"
    }
    
    # Check outbox processor status
    try:
        processor = get_processor()
        if processor.is_running():
            health_status["outbox_processor"] = "running"
            health_status["outbox_stats"] = processor.get_stats()
        else:
            health_status["outbox_processor"] = "stopped"
    except Exception as e:
        health_status["outbox_processor"] = f"error: {str(e)}"
    
    # Check drift consumer status
    if consumer_manager:
        try:
            status = consumer_manager.get_consumer_status()
            if status:
                # Check if any consumer has errors
                has_errors = any(s.startswith("Error") for s in status.values())
                health_status["drift_consumer"] = "error" if has_errors else "running"
                health_status["consumer_details"] = status
            else:
                health_status["drift_consumer"] = "not_registered"
        except Exception as e:
            health_status["drift_consumer"] = f"error: {str(e)}"
    else:
        health_status["drift_consumer"] = "not_started"
    
    # Determine overall status
    if (health_status["drift_consumer"] == "error" or 
        health_status["outbox_processor"] == "error"):
        health_status["status"] = "degraded"
    
    return health_status

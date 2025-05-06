import os 
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError  # For handling database-related errors
from sqlalchemy.orm import clear_mappers
#from .database import engine, Base

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

#load_dotenv()

logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="NTU FYP ACTIVITY SERVICE",
    description="This is the activity service api docs",
    version="0.1.0",
    servers=[],  # This removes the servers dropdown in Swagger UI
)

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the NTU FYP ACTIVITY SERVICE"}

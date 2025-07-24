from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
import app.crud.centre_activity_crud as crud 
import app.schemas.centre_activity_schema as schemas
from app.auth.jwt_utils import get_current_user_with_flag, JWTPayload, is_supervisor
from typing import Optional

router = APIRouter()


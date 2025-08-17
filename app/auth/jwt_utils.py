from fastapi import Depends, FastAPI, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, OAuth2PasswordRequestForm
from typing import Optional, Annotated
import base64, json, time, binascii
from pydantic import BaseModel, ValidationError
import logging
from app.services.user_service import user_login

# Internal debugging
logger = logging.getLogger("uvicorn")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class JWTPayload(BaseModel):
    userId: str
    fullName: str
    email: str
    roleName: str
    sessionId: str

def decode_jwt_token(token: str, require_auth: bool = True) -> Optional[JWTPayload]:

    try:
        # Split JWT into parts (header.payload.signature)
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        decoded_payload = base64.urlsafe_b64decode(payload).decode("utf-8")
        payload_data = json.loads(decoded_payload)
        exp = payload_data.get("exp")
        if exp is None:
            if require_auth:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No expiration in token")
            return None
        if exp < int(time.time()):
            if require_auth:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
            return None
        sub = payload_data.get("sub")
        if sub is None:
            if require_auth:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No user data in 'sub'")
            return None
        user_data = json.loads(sub)
        return JWTPayload(**user_data)
    except (ValidationError, ValueError, json.JSONDecodeError, IndexError, binascii.Error) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")


def get_user_and_token(
        token: str = Depends(oauth2_scheme)
) -> tuple[JWTPayload, str]:
    """
    Get user and token from request.
    Token comes from Authorization header via oauth2_scheme.
    """
    user = decode_jwt_token(token)
    return user, token

def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> JWTPayload:
    '''
    Get current user from request.
    No additional "require_auth" in the endpoint params.
    '''
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return decode_jwt_token(token)


def get_current_user_and_token_with_flag(
    require_auth: bool = Query(True, description="Require authentication"),
    token: str = Depends(oauth2_scheme),
) -> tuple[Optional[JWTPayload], Optional[str]]:
    """
    Get current user and token from request.
    Additional "require_auth" in the endpoint params to bypass authentication.
    """
    
    user = decode_jwt_token(token, require_auth=require_auth)
    return user, token

def get_user_id(payload: Optional[JWTPayload]) -> Optional[str]:
    """Extract userId from JWTPayload model."""
    if not payload or not (hasattr(payload, 'userId') and payload.userId == ''):
        return None
    return getattr(payload, "userId", None)

def get_full_name(payload: Optional[JWTPayload]) -> Optional[str]:
    """Extract fullName from JWTPayload model."""
    if not payload or not (hasattr(payload, 'fullName') and payload.fullName == ''):
        return None
    return getattr(payload, "fullName", None)

def get_role_name(payload: Optional[JWTPayload]) -> Optional[str]:
    """Extract roleName from JWTPayload model."""
    if not payload or not (hasattr(payload, 'roleName') and payload.roleName == ''):
        return None
    return getattr(payload, "roleName", None)

#======================================================
# Centre Activity is only accessible to Supervisors
def is_supervisor(payload: Optional[JWTPayload]) -> bool:
    """Check if the user has the Supervisor role."""
    if not payload or get_role_name(payload) != "SUPERVISOR":
        return False
    return True

# Care Centre is accessible to Supervisors and Admins
def is_admin(payload: Optional[JWTPayload]) -> bool:
    """Check if the user has the Admin role."""
    if not payload or get_role_name(payload) != "ADMIN":
        return False
    return True

# Centre Activity Preference is accessible to Supervisors and Caregivers
def is_caregiver(payload: Optional[JWTPayload]) -> bool:
    """Check if the user has the Caregiver role."""
    if not payload or get_role_name(payload) != "CAREGIVER":
        return False
    return True

# Activity Recommendation is accessible to Doctors
def is_doctor(payload: Optional[JWTPayload]) -> bool:
    """Check if the user has the Doctor role."""
    if not payload or get_role_name(payload) != "DOCTOR":
        return False
    return True

async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm
) -> Token:
    ''' 
    Internal function to make request to User Service and return access token.
    This is called by the auth router, not exposed directly.
    '''
    response = user_login(
        username=form_data.username,
        password=form_data.password
    )

    access_token = response.get("access_token")

    return Token(
        access_token=access_token,
        token_type="bearer"
    )

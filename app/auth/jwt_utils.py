from fastapi import Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from typing import Optional
import base64, json, time, binascii
from pydantic import BaseModel, ValidationError
from app.logger.config import logger
from fastapi.security.utils import get_authorization_scheme_param

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class JWTPayload(BaseModel):
    userId: str
    fullName: str
    email: str
    roleName: str
    sessionId: str

def decode_jwt_token(token: str, require_auth: bool = True) -> Optional[JWTPayload]:
    logger.debug(f"decode_jwt_token called with token={token}, require_auth={require_auth}")
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
        if require_auth:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")
        return None

async def optional_oauth2_scheme(request: Request) -> Optional[str]:
    """
    Custom dependency to optionally extract the token from the Authorization header.
    Does not raise 401 if token is missing.
    """
    authorization: str = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        return None
    return param

def get_current_user(
    token: str = Depends(optional_oauth2_scheme),
    require_auth: bool = True
) -> Optional[JWTPayload]:
    if not token and not require_auth:
        return None
    return decode_jwt_token(token, require_auth=require_auth)


def get_current_user_with_flag(
    require_auth: bool = Query(True, description="Require authentication"),
    token: Optional[str] = Depends(optional_oauth2_scheme)
) -> Optional[JWTPayload]:
    if token is None and require_auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if not token and not require_auth:
        return None
    return decode_jwt_token(token, require_auth=require_auth)

def get_user_id(payload: Optional[JWTPayload]) -> Optional[str]:
    """Extract userId from JWTPayload model."""
    if not payload or not hasattr(payload, 'userId') or payload.userId == '':
        return None
    return getattr(payload, "userId", None)

def get_full_name(payload: Optional[JWTPayload]) -> Optional[str]:
    """Extract fullName from JWTPayload model."""
    if not payload or not hasattr(payload, 'fullName') or payload.fullName == '':
        return None
    return getattr(payload, "fullName", None)

def get_role_name(payload: Optional[JWTPayload]) -> Optional[str]:
    """Extract roleName from JWTPayload model."""
    if not payload or not hasattr(payload, 'roleName') or payload.roleName == '':
        return None
    
    return getattr(payload, "roleName", None)

# Centre Activity is only accessible to Supervisors
def is_supervisor(payload: Optional[JWTPayload]) -> bool:
    """Check if the user has the Supervisor role."""
    if not payload or not hasattr(payload, 'roleName') or payload.roleName == '':
        return False
    return getattr(payload, "roleName", "").upper() == "SUPERVISOR"

# Care Centre is accessible to Supervisors and Admins
def is_admin(payload: Optional[JWTPayload]) -> bool:
    """Check if the user has the Admin role."""
    if not payload or not hasattr(payload, 'roleName') or payload.roleName == '':
        return False
    return getattr(payload, "roleName", "").upper() == "ADMIN"

# Centre Activity Preference is accessible to Supervisors and Caregivers
def is_caregiver(payload: Optional[JWTPayload]) -> bool:
    """Check if the user has the Caregiver role."""
    if not payload or not hasattr(payload, 'roleName') or payload.roleName == '':
        return False
    return getattr(payload, "roleName", "").upper() == "CAREGIVER"
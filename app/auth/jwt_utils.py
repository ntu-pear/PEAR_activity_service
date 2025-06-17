from fastapi import Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import base64, json, time, binascii
from pydantic import BaseModel, ValidationError
from app.logger.config import logger
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

def get_current_user(
    token: str = Depends(oauth2_scheme),
    require_auth: bool = True
) -> Optional[JWTPayload]:
    if not token and not require_auth:
        return None
    return decode_jwt_token(token, require_auth=require_auth)

def get_current_user_with_flag(
    require_auth: bool = Query(True),
    token: str = Depends(oauth2_scheme)
):
    logger.debug(f"get_current_user_with_flag called with require_auth={require_auth}, token={token}")
    if not token and not require_auth:
        return None
    return decode_jwt_token(token, require_auth=require_auth)
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.auth.jwt_utils import login_for_access_token, Token

router = APIRouter()

@router.post("/token", response_model=Token, include_in_schema=False)
async def authenticate_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    Internal login endpoint for backend testing only
    """
    return await login_for_access_token(form_data)

import pytest
from datetime import datetime, timedelta
import time
from app.auth.jwt_utils import decode_jwt_token, JWTPayload, get_user_id, get_full_name, get_role_name, is_supervisor, is_admin
from fastapi import HTTPException, status
from pydantic import ValidationError

@pytest.fixture
def mock_valid_token():
    '''
    Header:
    {
        "alg": "HS256",
        "typ": "JWT"
    }
    Payload:
    {
        "sub": "{\"userId\": 123, \"fullName\": \"John Doe\", \"roleName\": \"SUPERVISOR\", \"email\": \"john.doe@example.com\", \"sessionId\": \"abc123-session-id\"}",
        "exp": 33307301960         # Expiration time set far in the future for testing
    } 
    '''
    valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." \
    "eyJzdWIiOiJ7XCJ1c2VySWRcIjogXCIxXCIsIFwiZnVsbE5hbWV" \
    "cIjogXCJKb2huIERvZVwiLCBcInJvbGVOYW1lXCI6IFwiU1VQRV" \
    "JWSVNPUlwiLCBcImVtYWlsXCI6IFwiam9obi5kb2VAZXhhbXBsZ" \
    "S5jb21cIiwgXCJzZXNzaW9uSWRcIjogXCJhYmMxMjMtc2Vzc2lv" \
    "bi1pZFwifSIsImV4cCI6MzMzMDczMDE5NjB9.bZa7trgeLhMQkp" \
    "lH2gUQv_6r-BkPQz9O4iUejyGk4KE"
    return valid_token

@pytest.fixture
def mock_valid_payload():
    return JWTPayload(
        userId="123",
        fullName="John Doe",
        email="test@test.com",
        roleName="SUPERVISOR",
        sessionId="abc123"
    )


def test_decode_jwt_token_pass(mock_valid_token):
    payload = decode_jwt_token(mock_valid_token)
    assert isinstance(payload, JWTPayload)
    assert payload.userId == "1"
    assert payload.roleName == "SUPERVISOR"

def test_decode_jwt_token_no_exp():
    no_exp_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." \
    "eyJzdWIiOiJ7XCJ1c2VySWRcIjogXCIxXCIsIFwiZnVsbE5hbWVc" \
    "IjogXCJKb2huIERvZVwiLCBcInJvbGVOYW1lXCI6IFwiU1VQRVJW" \
    "SVNPUlwiLCBcImVtYWlsXCI6IFwiam9obi5kb2VAZXhhbXBsZS5j" \
    "b21cIiwgXCJzZXNzaW9uSWRcIjogXCJhYmMxMjMtc2Vzc2lvbi1p" \
    "ZFwifSJ9.y4czh4RQ1sFhNZQwxCRTgQuo4YVCcXIV7c8BW-4WnNM"

    with pytest.raises(HTTPException) as exc_info:
        decode_jwt_token(no_exp_token)
    assert exc_info.value.status_code == 401
    assert "No expiration in token" in str(exc_info.value.detail)
    
def test_decode_jwt_token_expired():
    expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ7XCJ1c2VySWRcIjogXCJ0ZXN0MTIzXCJ9IiwiZXhwIjogMH0.abc123"  # expired
    with pytest.raises(HTTPException) as exc_info:
        decode_jwt_token(expired_token)
    assert exc_info.value.status_code == 401
    assert "Token expired" in str(exc_info.value.detail)

def test_decode_jwt_token_no_user_data():
    no_user = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." \
    "eyJleHAiOjMzMzA3MzAxOTYwfQ.kmYY5tqr2Lc1ImRsahkK" \
    "gCE4DlNW8w74UNz_LuJJJAw"

    with pytest.raises(HTTPException) as exc_info:
        decode_jwt_token(no_user)
        assert exc_info.value.status_code == 401
        assert "No user data in 'sub'" in str(exc_info.value.detail)

def test_decode_jwt_token_invald():
    invalid_token = "invalidToken"
    with pytest.raises(HTTPException) as exc_info:
        decode_jwt_token(invalid_token)
    assert exc_info.value.status_code == 401
    assert "Invalid token" in str(exc_info.value.detail)

def test_get_user_id_pass(mock_valid_payload):
    assert get_user_id(mock_valid_payload) == "123"

def test_get_user_id_fail():
    with pytest.raises(ValidationError) as exc:
        invalid_payload = JWTPayload(
            fullName="John Doe",
            # Missing id
            email="test@test.com",
            roleName="SUPERVISOR",
            sessionId="abc123"
        )
        get_user_id(invalid_payload)
    assert "Field required" in str(exc.value)

def test_get_full_name_pass(mock_valid_payload):
    assert get_full_name(mock_valid_payload) == "John Doe"

def test_get_full_name_fail():
    ''' Raises Validation error when fullName is missing'''
    
    with pytest.raises(ValidationError) as exc:
        invalid_payload = JWTPayload(
            # Missing fullname
            userId="123",
            email="test@test.com",
            roleName="SUPERVISOR",
            sessionId="abc123"
        )
        get_full_name(invalid_payload)

    assert "Field required" in str(exc.value)

#==== Role Tests ====
def test_is_supervisor_pass(mock_valid_payload):
    assert is_supervisor(mock_valid_payload) is True

@pytest.mark.parametrize("role_name",
    ["ADMIN",
     "DOCTOR",
     "GUARDIAN",
     "GAME THERAPIST",
     "CAREGIVER",
     ])
def test_is_supervisor_fail(mock_valid_payload, role_name):
    mock_valid_payload.roleName = role_name
    assert is_supervisor(mock_valid_payload) is False

def test_is_admin_pass(mock_valid_payload):
    mock_valid_payload.roleName = "ADMIN"
    assert is_admin(mock_valid_payload) is True

@pytest.mark.parametrize("role_name",
    ["SUPERVISOR",
     "DOCTOR",
     "GUARDIAN",
     "GAME THERAPIST",
     "CAREGIVER",
     ])
def test_is_admin_fail(mock_valid_payload, role_name):
    mock_valid_payload.roleName = role_name
    assert is_admin(mock_valid_payload) is False
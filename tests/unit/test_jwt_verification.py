import base64
import json
import time

import pytest
from fastapi import HTTPException

from app.auth import jwt_utils, token_verifier
from app.auth.token_verifier import VerifiedUser


def _token(role="SUPERVISOR"):
    sub = json.dumps({"userId": "U1", "fullName": "Sam", "email": "s@example.com",
                      "roleName": role, "sessionId": "S1"})
    payload = json.dumps({"sub": sub, "exp": int(time.time()) + 3600}).encode()
    return "eyJhbGciOiJIUzI1NiJ9." + base64.urlsafe_b64encode(payload).decode().rstrip("=") + ".sig"


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.delenv("AUTH_VERIFY_MODE", raising=False)
    token_verifier.reset_cache()


def test_shadow_keeps_claimed_identity(monkeypatch):
    calls = []
    monkeypatch.setattr(jwt_utils, "apply_verification", lambda **kw: calls.append(kw) or None)
    payload = jwt_utils.decode_jwt_token(_token(role="ADMIN"), endpoint="/routines")
    assert payload.roleName == "ADMIN"
    assert calls[0]["endpoint"] == "/routines"


def test_enforce_uses_verified_identity(monkeypatch):
    monkeypatch.setattr(jwt_utils, "apply_verification",
                        lambda **kw: VerifiedUser("U1", "Sam (verified)", "SUPERVISOR", "s@example.com"))
    payload = jwt_utils.decode_jwt_token(_token())
    assert payload.fullName == "Sam (verified)" and payload.sessionId == "S1"


def test_enforce_rejection_returns_none_when_auth_optional(monkeypatch):
    def reject(**kw):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    monkeypatch.setattr(jwt_utils, "apply_verification", reject)
    assert jwt_utils.decode_jwt_token(_token(), require_auth=False) is None
    with pytest.raises(HTTPException):
        jwt_utils.decode_jwt_token(_token(), require_auth=True)

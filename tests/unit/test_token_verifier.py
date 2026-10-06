import logging

import httpx
import pytest
from fastapi import HTTPException

from app.auth import token_verifier
from app.auth.token_verifier import Verdict, VerifiedUser, apply_verification, record_auth_bypass, verify_token

USER = {"userId": "U1", "fullName": "Sam", "roleName": "SUPERVISOR", "email": "s@example.com"}


@pytest.fixture(autouse=True)
def _configured(monkeypatch):
    monkeypatch.setenv("USER_BE_ORIGIN", "http://user-svc")
    monkeypatch.delenv("AUTH_VERIFY_MODE", raising=False)
    token_verifier.reset_cache()
    yield
    token_verifier.reset_cache()


def _respond(monkeypatch, status, body=None):
    monkeypatch.setattr(token_verifier, "_call_user_service",
                        lambda base_url, token: httpx.Response(status, json=body if body is not None else {}))


def test_verify_valid(monkeypatch):
    _respond(monkeypatch, 200, USER)
    verdict, user = verify_token("tok", now=lambda: 1.0)
    assert verdict == Verdict.VALID and user.roleName == "SUPERVISOR"


def test_network_error_backs_off(monkeypatch):
    calls = []

    def boom(base_url, token):
        calls.append(token)
        raise httpx.ConnectError("down")

    monkeypatch.setattr(token_verifier, "_call_user_service", boom)
    verify_token("a", now=lambda: 1000.0)
    verify_token("b", now=lambda: 1010.0)
    assert calls == ["a"]


def test_shadow_logs_forged_role_and_returns_none(monkeypatch, caplog):
    _respond(monkeypatch, 200, USER)
    with caplog.at_level(logging.WARNING, logger="pear.auth"):
        result = apply_verification("tok", claimed_user_id="U1", claimed_role="ADMIN", endpoint="/routines")
    assert result is None
    record = caplog.records[-1]
    assert record.auth_event == "would_reject"
    assert record.auth_reason == "identity_mismatch"
    assert record.auth_endpoint == "/routines"


def test_shadow_logs_rejected_token(monkeypatch, caplog):
    _respond(monkeypatch, 401)
    with caplog.at_level(logging.WARNING, logger="pear.auth"):
        assert apply_verification("tok", "U1", "SUPERVISOR", "/x") is None
    assert caplog.records[-1].auth_reason == "token_rejected"


def test_shadow_valid_logs_nothing(monkeypatch, caplog):
    _respond(monkeypatch, 200, USER)
    with caplog.at_level(logging.WARNING, logger="pear.auth"):
        assert apply_verification("tok", "U1", "SUPERVISOR", "/x") is None
    assert caplog.records == []


def test_enforce_returns_verified_user(monkeypatch):
    monkeypatch.setenv("AUTH_VERIFY_MODE", "enforce")
    _respond(monkeypatch, 200, USER)
    assert apply_verification("tok", "U1", "SUPERVISOR", "/x") == VerifiedUser("U1", "Sam", "SUPERVISOR", "s@example.com")


def test_enforce_rejects_forged_role(monkeypatch):
    monkeypatch.setenv("AUTH_VERIFY_MODE", "enforce")
    _respond(monkeypatch, 200, USER)
    with pytest.raises(HTTPException) as exc:
        apply_verification("tok", "U1", "ADMIN", "/x")
    assert exc.value.status_code == 401


def test_enforce_unavailable_is_503(monkeypatch):
    monkeypatch.setenv("AUTH_VERIFY_MODE", "enforce")
    _respond(monkeypatch, 502)
    with pytest.raises(HTTPException) as exc:
        apply_verification("tok", "U1", "SUPERVISOR", "/x")
    assert exc.value.status_code == 503


def test_invalid_mode_falls_back_to_shadow(monkeypatch):
    monkeypatch.setenv("AUTH_VERIFY_MODE", "nonsense")
    _respond(monkeypatch, 401)
    assert apply_verification("tok", "U1", "SUPERVISOR", "/x") is None


def test_unconfigured_shadow_is_silent(monkeypatch, caplog):
    monkeypatch.delenv("USER_BE_ORIGIN", raising=False)
    with caplog.at_level(logging.WARNING, logger="pear.auth"):
        assert apply_verification("tok", "U1", "SUPERVISOR", "/x") is None
    assert caplog.records == []


def test_record_auth_bypass(caplog):
    with caplog.at_level(logging.WARNING, logger="pear.auth"):
        record_auth_bypass("/centre_activity_preferences")
    assert caplog.records[-1].auth_reason == "require_auth_false"


def _malformed_200(monkeypatch):
    monkeypatch.setattr(token_verifier, "_call_user_service",
                        lambda base_url, token: httpx.Response(200, content=b"not json"))


def test_malformed_200_is_unavailable(monkeypatch):
    _malformed_200(monkeypatch)
    assert verify_token("tok", now=lambda: 1.0) == (Verdict.UNAVAILABLE, None)


def test_shadow_malformed_200_returns_none_without_raising(monkeypatch):
    _malformed_200(monkeypatch)
    assert apply_verification("tok", "U1", "SUPERVISOR", "/x") is None

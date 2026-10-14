"""X-Request-ID is forwarded on Activity's outbound calls only when ops logging provides one."""
from unittest.mock import MagicMock

import httpx
import pytest
import requests

from app.auth import token_verifier
from app.services import patient_service, user_service


@pytest.fixture
def captured(monkeypatch):
    seen = {}

    def fake(url, headers=None, **kwargs):
        seen["url"], seen["headers"] = url, headers
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"access_token": "t", "data": {"name": "P"}}
        return response

    monkeypatch.setattr(requests, "get", fake)
    monkeypatch.setattr(requests, "post", fake)
    monkeypatch.setattr(httpx, "get", fake)
    return seen


@pytest.mark.parametrize("call", [patient_service.get_patient_by_id, patient_service.get_patient_allocation_by_patient_id])
def test_patient_calls_unchanged_when_ops_logging_is_off(captured, call):
    call(require_auth=True, bearer_token="tok", patient_id=1)
    assert captured["headers"] == {"Authorization": "Bearer tok"}
    call(require_auth=False, bearer_token="tok", patient_id=1)
    assert captured["headers"] is None


@pytest.mark.parametrize("call", [patient_service.get_patient_by_id, patient_service.get_patient_allocation_by_patient_id])
def test_patient_calls_forward_request_id(captured, monkeypatch, call):
    monkeypatch.setattr(patient_service, "outbound_headers", lambda: {"X-Request-ID": "rid-1"})
    call(require_auth=True, bearer_token="tok", patient_id=1)
    assert captured["headers"] == {"X-Request-ID": "rid-1", "Authorization": "Bearer tok"}
    call(require_auth=False, bearer_token="tok", patient_id=1)
    assert captured["headers"] == {"X-Request-ID": "rid-1"}


def test_login_passthrough_headers(captured, monkeypatch):
    user_service.user_login("someone@example.com", "pw")
    assert captured["headers"] is None
    monkeypatch.setattr(user_service, "outbound_headers", lambda: {"X-Request-ID": "rid-2"})
    user_service.user_login("someone@example.com", "pw")
    assert captured["headers"] == {"X-Request-ID": "rid-2"}


def test_token_verification_call_headers(captured, monkeypatch):
    token_verifier._call_user_service("http://user-service", "tok")
    assert captured["headers"] == {"Authorization": "Bearer tok"}
    monkeypatch.setattr(token_verifier, "outbound_headers", lambda: {"X-Request-ID": "rid-3"})
    token_verifier._call_user_service("http://user-service", "tok")
    assert captured["headers"] == {"Authorization": "Bearer tok", "X-Request-ID": "rid-3"}

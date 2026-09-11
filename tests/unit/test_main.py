import pytest

from app.main import _is_bypass_auth_enabled


def test_bypass_auth_disabled_when_env_var_unset(monkeypatch):
    """No BYPASS_AUTH set at all -> bypass stays off"""
    monkeypatch.delenv("BYPASS_AUTH", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    assert _is_bypass_auth_enabled() is False


def test_bypass_auth_disabled_when_explicitly_false(monkeypatch):
    """BYPASS_AUTH=false -> bypass off regardless of ENVIRONMENT"""
    monkeypatch.setenv("BYPASS_AUTH", "false")
    monkeypatch.setenv("ENVIRONMENT", "local")

    assert _is_bypass_auth_enabled() is False


def test_bypass_auth_true_without_environment_var_refuses_to_start(monkeypatch):
    """BYPASS_AUTH=true with no ENVIRONMENT set (defaults to production) -> hard fail"""
    monkeypatch.setenv("BYPASS_AUTH", "true")
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    with pytest.raises(RuntimeError, match="ENVIRONMENT=local"):
        _is_bypass_auth_enabled()


@pytest.mark.parametrize("environment", ["staging", "production", "dev", "PRODUCTION"])
def test_bypass_auth_true_in_non_local_environment_refuses_to_start(monkeypatch, environment):
    """BYPASS_AUTH=true outside a local environment -> hard fail, never silently on or off"""
    monkeypatch.setenv("BYPASS_AUTH", "true")
    monkeypatch.setenv("ENVIRONMENT", environment)

    with pytest.raises(RuntimeError, match="ENVIRONMENT=local"):
        _is_bypass_auth_enabled()


def test_bypass_auth_true_with_local_environment_is_allowed(monkeypatch):
    """The only combination that actually enables bypass: both flags explicitly local"""
    monkeypatch.setenv("BYPASS_AUTH", "true")
    monkeypatch.setenv("ENVIRONMENT", "local")

    assert _is_bypass_auth_enabled() is True


def test_bypass_auth_flags_are_case_insensitive(monkeypatch):
    monkeypatch.setenv("BYPASS_AUTH", "TRUE")
    monkeypatch.setenv("ENVIRONMENT", "LOCAL")

    assert _is_bypass_auth_enabled() is True

"""main.py wires ops logging, and it stays dark unless OPS_LOGGING is on.

Importing app.main is safe here: the lifespan (outbox processor, consumers)
only starts under a running server or a TestClient context manager.
"""
import inspect

import pytest

import app.main as main
from app import ops_logging


def test_ops_logging_is_off_by_default():
    if ops_logging.is_enabled():
        pytest.skip("OPS_LOGGING is on in this shell")
    assert all(m.cls is not ops_logging.OpsRequestMiddleware for m in main.app.user_middleware)


def test_main_calls_setup_last_with_the_activity_service_name():
    source = inspect.getsource(main)
    call = 'setup_ops_logging(app, service="activity", log_dir=LOG_DIR)'
    assert call in source
    assert source.index(call) > source.rindex("add_middleware(")

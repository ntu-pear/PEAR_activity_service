from unittest.mock import patch

import pytest

from app.logger import reference_names as rn
from app.logger.logger_utils import ActionType, log_crud_action, filter_data


@pytest.fixture(autouse=True)
def clear_cache():
    rn._cache.clear()
    yield
    rn._cache.clear()


def fake_fetch(kind, ids):
    table = {
        "activity": {1: "Gardening"},
        "centre_activity": {10: "Painting", 11: "Singing"},
        "routine": {5: "Morning Walk"},
    }[kind]
    return {i: table[i] for i in ids if i in table}


def run(data):
    with patch.object(rn, "_fetch_names", side_effect=fake_fetch):
        return rn.add_reference_names(data)


def test_activity_id_maps_to_activity_name():
    assert run({"activity_id": 1})["activity_name"] == "Gardening"


def test_centre_activity_keys_map_to_activity_title():
    out = run({"centre_activity_id": 10, "old_centre_activity_id": 10, "new_centre_activity_id": 11})
    assert out["centre_activity_name"] == "Painting"
    assert out["old_centre_activity_name"] == "Painting"
    assert out["new_centre_activity_name"] == "Singing"


def test_routine_id_maps_to_routine_name():
    assert run({"routine_id": 5})["routine_name"] == "Morning Walk"


def test_unknown_id_adds_nothing():
    out = run({"activity_id": 999, "routine_id": 999})
    assert out == {"activity_id": 999, "routine_id": 999}


def test_existing_name_key_not_overwritten():
    out = run({"activity_id": 1, "activity_name": "Custom"})
    assert out["activity_name"] == "Custom"


def test_original_dict_not_mutated():
    data = {"activity_id": 1}
    run(data)
    assert data == {"activity_id": 1}


def test_exception_returns_data_unchanged():
    data = {"activity_id": 1}
    with patch.object(rn, "_fetch_names", side_effect=RuntimeError("db down")):
        assert rn.add_reference_names(data) == {"activity_id": 1}


def test_no_known_key_means_no_lookup():
    with patch.object(rn, "_fetch_names") as m:
        assert rn.add_reference_names({"title": "x"}) == {"title": "x"}
        m.assert_not_called()


def test_none_and_non_dict_passthrough():
    assert rn.add_reference_names(None) is None
    assert rn.add_reference_names("x") == "x"


def test_results_cached():
    with patch.object(rn, "_fetch_names", side_effect=fake_fetch) as m:
        rn.add_reference_names({"activity_id": 1})
        rn.add_reference_names({"activity_id": 1})
        assert m.call_count == 1


def test_cache_expires():
    with patch.object(rn, "_fetch_names", side_effect=fake_fetch) as m:
        rn.add_reference_names({"activity_id": 1})
        for k, (ts, v) in list(rn._cache.items()):
            rn._cache[k] = (ts - rn.CACHE_TTL_SECONDS - 1, v)
        rn.add_reference_names({"activity_id": 1})
        assert m.call_count == 2


def test_created_by_ids_kept_by_filter():
    out = filter_data({"CreatedById": "u1", "ModifiedById": "u2", "created_by_id": "u3"})
    assert out == {"CreatedById": "u1", "ModifiedById": "u2", "created_by_id": "u3"}


def test_log_crud_action_enriches_both_sides():
    with patch.object(rn, "_fetch_names", side_effect=fake_fetch), \
         patch("app.logger.logger_utils.logger") as lg:
        log_crud_action(ActionType.UPDATE, "u", "U", "m", "ROUTINE", 1,
                        original_data={"routine_id": 5}, updated_data={"activity_id": 1})
    data = lg.info.call_args[0][0]
    assert data["original_data"]["routine_name"] == "Morning Walk"
    assert data["updated_data"]["activity_name"] == "Gardening"


def test_lookup_session_sets_lock_timeout_first():
    from unittest.mock import MagicMock
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [(1, "Gardening")]
    with patch("app.database.SessionLocal", return_value=db):
        assert rn._fetch_names("activity", [1]) == {1: "Gardening"}
    first = db.execute.call_args_list[0][0][0]
    assert "LOCK_TIMEOUT 500" in str(first)
    assert db.execute.call_args_list[0] == db.method_calls[0]
    db.close.assert_called_once()


def test_lock_timeout_error_returns_data_unchanged():
    from unittest.mock import MagicMock
    db = MagicMock()
    db.query.return_value.filter.return_value.all.side_effect = Exception("Lock request time out period exceeded")
    data = {"activity_id": 1}
    with patch("app.database.SessionLocal", return_value=db):
        assert rn.add_reference_names(data) == {"activity_id": 1}
    db.close.assert_called_once()


def test_lock_timeout_reset_even_when_query_raises():
    from unittest.mock import MagicMock
    db = MagicMock()
    db.query.return_value.filter.return_value.all.side_effect = Exception("boom")
    with patch("app.database.SessionLocal", return_value=db):
        with pytest.raises(Exception):
            rn._fetch_names("activity", [1])
    stmts = [str(c[0][0]) for c in db.execute.call_args_list]
    assert "LOCK_TIMEOUT 500" in stmts[0]
    assert "LOCK_TIMEOUT -1" in stmts[-1]
    db.close.assert_called_once()
